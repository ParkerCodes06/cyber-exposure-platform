from backend.app.utils.logger import get_logger

logger = get_logger("risk_engine")


def severity_score(severity: str):
    mapping = {
        "LOW": 2,
        "MEDIUM": 5,
        "HIGH": 8,
        "CRITICAL": 10
    }
    return mapping.get(severity.upper(), 1)


def port_risk(port: int):
    risky_ports = {
        22: 6,
        80: 5,
        443: 5,
        3389: 9
    }
    return risky_ports.get(port, 3)


def calculate_risk(vulns, open_ports):
    total_score = 0
    scored_items = []

    for v in vulns:
        sev = severity_score(v["severity"])

        exposure = sum(port_risk(p) for p in open_ports) / max(len(open_ports), 1)

        score = sev * exposure

        # exploit boost
        if v["severity"].upper() == "CRITICAL" and 3389 in open_ports:
            score *= 1.5

        scored_items.append({
            "cve_id": v["cve_id"],
            "software": v["software"],
            "severity": v["severity"],
            "risk_score": round(score, 2),
            "description": v["description"]
        })

        total_score += score

    scored_items.sort(key=lambda x: x["risk_score"], reverse=True)

    logger.info(f"Risk calculated: {classify(total_score)} (score: {total_score})")

    return {
        "total_risk_score": round(total_score, 2),
        "risk_level": classify(total_score),
        "findings": scored_items
    }


def classify(score):
    if score >= 50:
        return "CRITICAL"
    elif score >= 30:
        return "HIGH"
    elif score >= 15:
        return "MEDIUM"
    else:
        return "LOW"
