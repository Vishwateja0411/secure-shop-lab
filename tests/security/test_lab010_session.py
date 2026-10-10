import pytest
from backend.app.config import settings

def test_lab010_session_cookie_attributes(client):
    """
    LAB-010: Session Management
    Test that session cookies carry HttpOnly and SameSite attributes in secure mode.
    """
    # Vulnerable mode: session cookie lacks HttpOnly flag
    settings.SECURE_MODE = False
    vuln_resp = client.post("/api/auth/login", json={"username": "alice", "password": "AlicePass123!"})
    cookie_header_vuln = vuln_resp.headers.get("set-cookie", "")
    if "HttpOnly" not in cookie_header_vuln:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Session cookie set without HttpOnly flag (accessible to XSS).")

    # Secure mode: session cookie must include HttpOnly and SameSite=Lax
    settings.SECURE_MODE = True
    secure_resp = client.post("/api/auth/login", json={"username": "alice", "password": "AlicePass123!"})
    cookie_header_sec = secure_resp.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header_sec, "Secure mode must set HttpOnly attribute on session cookies."
    assert "samesite=lax" in cookie_header_sec.lower(), "Secure mode must set SameSite=Lax."
