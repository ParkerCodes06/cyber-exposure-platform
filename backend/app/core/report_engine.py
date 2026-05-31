from backend.app.utils.logger import get_logger

logger = get_logger("report_engine")


def generate_report(hostname, os_value, risk_report, attack_path):

    risk_level = risk_report["risk_level"]
    total_score = risk_report["total_risk_score"]

    # 1. Executive Summary (business-friendly)
    summary = f"""
    System {hostname} is currently assessed as {risk_level} risk.
    Total exposure score is {total_score}.
    Immediate remediation is required for critical findings.
    """

    # 2. Critical findings extraction
    critical = [
        f"{f['cve_id']} - {f['description']}"
        for f in risk_report["findings"]
        if f["severity"] == "CRITICAL"
    ]

    # 3. Remediation mapping (simple rule-based)
    remediation = []

    for f in risk_report["findings"]:
        if "openssl" in f["software"].lower():
            remediation.append("Update OpenSSL to latest stable version")

        if "apache" in f["software"].lower():
            remediation.append("Patch Apache HTTP Server immediately")

    # 4. Attack summary compression
    attack_summary = [
        f"{step['stage']} -> {step['technique']}"
        for step in attack_path
    ]

    logger.info(f"Report generated for {hostname}: {risk_level}")
    return {
        "executive_summary": summary,
        "risk_overview": {
            "level": risk_level,
            "score": total_score
        },
        "critical_findings": critical,
        "attack_paths": attack_summary,
        "remediation_plan": list(set(remediation))
    }
