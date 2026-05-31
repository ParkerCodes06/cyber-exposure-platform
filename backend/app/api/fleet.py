import json
from fastapi import APIRouter, HTTPException
from backend.app.db.database import get_connection
from backend.app.core.cve_engine import check_vulnerabilities
from backend.app.core.risk_engine import calculate_risk
from backend.app.utils.logger import get_logger

logger = get_logger("api.fleet")
router = APIRouter()


@router.get("/fleet/summary")
def fleet_summary():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        rows = cursor.fetchall()

        total_assets = len(rows)
        critical_assets = 0
        overall_score = 0
        all_vulns = []

        for row in rows:
            os_value = row["os"]
            open_ports = json.loads(row["open_ports"] or "[]")
            vulnerabilities = check_vulnerabilities(os_value=os_value)
            risk_report = calculate_risk(vulnerabilities, open_ports)

            level = risk_report["risk_level"]
            score = risk_report["total_risk_score"]

            if level == "CRITICAL":
                critical_assets += 1

            overall_score += score

            for finding in risk_report["findings"]:
                all_vulns.append({
                    "cve_id": finding["cve_id"],
                    "software": finding["software"],
                    "severity": finding["severity"],
                    "risk_score": finding["risk_score"]
                })

        avg_risk = round(overall_score / max(total_assets, 1), 2)

        all_vulns.sort(key=lambda x: x["risk_score"], reverse=True)
        top_vulns = all_vulns[:10]

        conn.close()

        logger.info(f"Fleet summary: {total_assets} assets, avg risk {avg_risk}")
        return {
            "total_assets": total_assets,
            "critical_assets": critical_assets,
            "average_risk": avg_risk,
            "top_vulnerabilities": top_vulns
        }
    except Exception as e:
        logger.error(f"Fleet summary failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fleet/assets")
def fleet_assets():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        rows = cursor.fetchall()

        assets = []
        for row in rows:
            os_value = row["os"]
            open_ports = json.loads(row["open_ports"] or "[]")
            vulnerabilities = check_vulnerabilities(os_value=os_value)
            risk_report = calculate_risk(vulnerabilities, open_ports)

            assets.append({
                "hostname": row["hostname"],
                "agent_id": row["agent_id"],
                "os": row["os"],
                "ip_address": row["ip_address"],
                "last_seen": row["last_seen"],
                "risk_level": risk_report["risk_level"],
                "score": risk_report["total_risk_score"]
            })

        assets.sort(key=lambda x: x["score"], reverse=True)

        conn.close()

        logger.info(f"Fleet assets returned: {len(assets)}")
        return assets
    except Exception as e:
        logger.error(f"Fleet assets failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fleet/risk-trends")
def fleet_risk_trends():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT hostname, timestamp, risk_score, risk_level
            FROM scan_history
            ORDER BY timestamp ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        trends = {}
        for row in rows:
            hostname = row["hostname"]
            if hostname not in trends:
                trends[hostname] = []
            trends[hostname].append({
                "timestamp": row["timestamp"],
                "risk_score": row["risk_score"],
                "risk_level": row["risk_level"]
            })

        result = [
            {"hostname": hostname, "entries": entries}
            for hostname, entries in trends.items()
        ]

        logger.info(f"Risk trends returned for {len(result)} hosts")
        return result
    except Exception as e:
        logger.error(f"Risk trends failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
