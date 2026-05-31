import json
from fastapi import APIRouter, HTTPException
from backend.app.db.database import get_connection
from backend.app.core.cve_engine import check_vulnerabilities
from backend.app.core.risk_engine import calculate_risk
from backend.app.utils.logger import get_logger

logger = get_logger("api.dashboard")
router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        rows = cursor.fetchall()
        conn.close()

        total_assets = len(rows)
        critical_risks = 0
        high_risks = 0
        overall_score = 0

        for row in rows:
            os_value = row["os"]
            open_ports = json.loads(row["open_ports"] or "[]")
            vulnerabilities = check_vulnerabilities(os_value=os_value)
            risk_report = calculate_risk(vulnerabilities, open_ports)

            level = risk_report["risk_level"]
            score = risk_report["total_risk_score"]

            if level == "CRITICAL":
                critical_risks += 1
            elif level == "HIGH":
                high_risks += 1

            overall_score += score

        avg_score = round(overall_score / max(total_assets, 1), 2)

        logger.info(f"Dashboard summary: {total_assets} assets, avg score {avg_score}")
        return {
            "total_assets": total_assets,
            "critical_risks": critical_risks,
            "high_risks": high_risks,
            "overall_score": avg_score
        }
    except Exception as e:
        logger.error(f"Dashboard summary failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard/assets")
def dashboard_assets():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        rows = cursor.fetchall()
        conn.close()

        assets = []
        for row in rows:
            os_value = row["os"]
            open_ports = json.loads(row["open_ports"] or "[]")
            vulnerabilities = check_vulnerabilities(os_value=os_value)
            risk_report = calculate_risk(vulnerabilities, open_ports)

            assets.append({
                "hostname": row["hostname"],
                "risk_level": risk_report["risk_level"],
                "score": risk_report["total_risk_score"]
            })

        assets.sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"Dashboard assets returned: {len(assets)}")
        return assets
    except Exception as e:
        logger.error(f"Dashboard assets failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard/top-risks")
def dashboard_top_risks():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        rows = cursor.fetchall()
        conn.close()

        top_risks = []
        for row in rows:
            os_value = row["os"]
            open_ports = json.loads(row["open_ports"] or "[]")
            vulnerabilities = check_vulnerabilities(os_value=os_value)
            risk_report = calculate_risk(vulnerabilities, open_ports)

            for finding in risk_report["findings"][:2]:
                top_risks.append({
                    "hostname": row["hostname"],
                    "finding": f"{finding['cve_id']} - {finding['software']}"
                })

        top_risks.sort(key=lambda x: x["hostname"])

        logger.info(f"Top risks returned: {len(top_risks)}")
        return top_risks
    except Exception as e:
        logger.error(f"Dashboard top-risks failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
