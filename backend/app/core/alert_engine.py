from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("alert_engine")


def _insert_alert(conn, tenant_id, hostname, alert_type, message, severity):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (tenant_id, hostname, alert_type, message, severity)
        VALUES (?, ?, ?, ?, ?)
    """, (tenant_id, hostname, alert_type, message, severity))
    logger.warning(f"ALERT [{severity}] {alert_type}: {message} (tenant={tenant_id}, host={hostname})")


def check_and_alert(tenant_id, hostname, risk_report, vulnerabilities, previous_score):
    try:
        conn = get_connection()

        current_level = risk_report["risk_level"]
        current_score = risk_report["total_risk_score"]

        if current_level == "CRITICAL":
            _insert_alert(
                conn, tenant_id, hostname,
                "CRITICAL_RISK",
                f"{hostname} is now CRITICAL risk (score: {current_score})",
                "CRITICAL"
            )
        elif current_level == "HIGH":
            _insert_alert(
                conn, tenant_id, hostname,
                "HIGH_RISK",
                f"{hostname} is HIGH risk (score: {current_score})",
                "HIGH"
            )

        if previous_score > 0 and current_score > previous_score * 1.5:
            _insert_alert(
                conn, tenant_id, hostname,
                "RISK_SPIKE",
                f"{hostname} risk spiked from {previous_score} to {current_score} ({round((current_score/previous_score - 1)*100)}% increase)",
                "HIGH"
            )

        if previous_score == 0 and current_score > 0:
            _insert_alert(
                conn, tenant_id, hostname,
                "NEW_FINDINGS",
                f"{hostname} has {len(vulnerabilities)} new vulnerability findings",
                "MEDIUM"
            )

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Alert check failed for {hostname}: {e}")


def get_alerts(tenant_id, limit=50):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alerts
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (tenant_id, limit))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "hostname": row["hostname"],
                "alert_type": row["alert_type"],
                "message": row["message"],
                "severity": row["severity"],
                "created_at": row["created_at"],
                "acknowledged": bool(row["acknowledged"])
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Alert retrieval failed: {e}")
        return []


def acknowledge_alert(alert_id, tenant_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alerts SET acknowledged = 1
            WHERE id = ? AND tenant_id = ?
        """, (alert_id, tenant_id))

        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Alert acknowledgment failed: {e}")
        return False
