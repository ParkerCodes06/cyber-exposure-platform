import json
from fastapi import APIRouter, HTTPException, Header
from backend.app.db.database import get_connection
from backend.app.core.cve_engine import check_vulnerabilities
from backend.app.core.risk_engine import calculate_risk
from backend.app.core.attack_engine import build_attack_path
from backend.app.core.report_engine import generate_report
from backend.app.utils.logger import get_logger

logger = get_logger("api.scan")
router = APIRouter()

API_KEY = "secret-key-change-me"


def verify_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/scan/{hostname}")
def scan_host(hostname: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM assets WHERE hostname = ?
        """, (hostname,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": "Host not found"}

        os_value = row["os"]
        open_ports = json.loads(row["open_ports"] or "[]")

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

        logger.info(f"Scan completed for {hostname}")
        return {
            "hostname": hostname,
            "report": final_report
        }
    except Exception as e:
        logger.error(f"Scan failed for {hostname}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/attack-path/{hostname}")
def attack_path(hostname: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets WHERE hostname = ?", (hostname,))
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

        logger.info(f"Attack path built for {hostname}")
        return {
            "hostname": hostname,
            "attack_path": path,
            "stages": len(path)
        }
    except Exception as e:
        logger.error(f"Attack path failed for {hostname}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
