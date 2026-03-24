from enterprise_mcp.server import classify_incident


def test_classify_incident_p1() -> None:
    result = classify_incident("critical", "production-down")
    assert result["priority"] == "P1"


def test_classify_incident_p3() -> None:
    result = classify_incident("low", "single-team")
    assert result["priority"] == "P3"
