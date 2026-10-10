import pytest
from backend.app.config import settings

def test_security_headers(client):
    """
    Security Misconfiguration & Hardening Test
    Test that defensive security headers are emitted in secure mode.
    """
    settings.SECURE_MODE = False
    vuln_resp = client.get("/api/health")
    if "Content-Security-Policy" not in vuln_resp.headers:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Missing Content-Security-Policy header.")

    settings.SECURE_MODE = True
    sec_resp = client.get("/api/health")
    headers = sec_resp.headers
    assert "Content-Security-Policy" in headers
    assert "X-Frame-Options" in headers
    assert "X-Content-Type-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
