def test_risk_engine_empty():
    from backend.app.core.risk_engine import calculate_risk
    result = calculate_risk([], [80])
    assert result["total_risk_score"] >= 0


def test_risk_engine_with_vulns():
    from backend.app.core.risk_engine import calculate_risk
    vulns = [
        {"cve_id": "CVE-2024-0001", "software": "openssl", "severity": "HIGH", "description": "test"}
    ]
    result = calculate_risk(vulns, [3389, 80])
    assert result["total_risk_score"] > 0
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_severity_score():
    from backend.app.core.risk_engine import severity_score
    assert severity_score("LOW") == 2
    assert severity_score("MEDIUM") == 5
    assert severity_score("HIGH") == 8
    assert severity_score("CRITICAL") == 10
    assert severity_score("UNKNOWN") == 1


def test_classify():
    from backend.app.core.risk_engine import classify
    assert classify(0) == "LOW"
    assert classify(15) == "MEDIUM"
    assert classify(30) == "HIGH"
    assert classify(50) == "CRITICAL"
