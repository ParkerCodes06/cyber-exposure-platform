import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from backend.app.db.database import get_connection
from backend.app.core.cve_engine import check_vulnerabilities
from backend.app.core.risk_engine import calculate_risk
from backend.app.core.attack_engine import build_attack_path
from backend.app.core.report_engine import generate_report
from backend.app.core.alert_engine import check_and_alert
from backend.app.core.deps import get_current_user
from backend.app.utils.logger import get_logger

logger = get_logger("api.scan")
router = APIRouter()


@router.get("/scan/{hostname}")
def scan_host(hostname: str, user: dict = Depends(get_current_user)):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        tenant_id = user["tenant_id"]

        cursor.execute("""
            SELECT * FROM assets WHERE hostname = ? AND tenant_id = ?
        """, (hostname, tenant_id))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return {"error": "Host not found"}

        os_value = row["os"]
        open_ports = json.loads(row["open_ports"] or "[]")
        agent_id = row["agent_id"] or hostname
        previous_score = row["risk_score"] or 0

        vulnerabilities = check_vulnerabilities(os_value=os_value)

        risk_report = calculate_risk(vulnerabilities, open_ports)

        attack_path = build_attack_path(
            os_value=os_value,
            open_ports=open_ports,
            vulnerabilities=vulnerabilities
        )

        final_report = generate_report(
            hostname,
            os_value,
            risk_report,
            attack_path
        )

        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO scan_history (hostname, agent_id, timestamp, risk_score,
                vulnerability_count, risk_level, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            hostname,
            agent_id,
            now,
            risk_report["total_risk_score"],
            len(vulnerabilities),
            risk_report["risk_level"],
            tenant_id
        ))

        cursor.execute("""
            UPDATE assets SET last_seen = ?, risk_score = ?, risk_level = ?
            WHERE hostname = ? AND tenant_id = ?
        """, (now, risk_report["total_risk_score"], risk_report["risk_level"], hostname, tenant_id))

        conn.commit()
        conn.close()

        check_and_alert(tenant_id, hostname, risk_report, vulnerabilities, previous_score)

        logger.info(f"Scan completed for {hostname} (tenant={tenant_id})")
        return {
            "hostname": hostname,
            "report": final_report
        }
    except Exception as e:
        logger.error(f"Scan failed for {hostname}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/attack-path/{hostname}")
def attack_path(hostname: str, user: dict = Depends(get_current_user)):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        tenant_id = user["tenant_id"]

        cursor.execute("SELECT * FROM assets WHERE hostname = ? AND tenant_id = ?", (hostname, tenant_id))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": "Host not found"}

        os_value = row["os"]
        open_ports = json.loads(row["open_ports"] or "[]")

        vulnerabilities = check_vulnerabilities(os_value=os_value)

        path = build_attack_path(
            os_value=os_value,
            open_ports=open_ports,
            vulnerabilities=vulnerabilities
        )

        logger.info(f"Attack path built for {hostname} (tenant={tenant_id})")
        return {
            "hostname": hostname,
            "attack_path": path,
            "stages": len(path)
        }
    except Exception as e:
        logger.error(f"Attack path failed for {hostname}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
