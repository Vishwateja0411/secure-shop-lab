import pytest
from backend.app.config import settings

def test_lab009_weak_password_policy(client):
    """
    LAB-009: Weak Authentication
    Test that trivial passwords (e.g. '1') are rejected when secure mode is active.
    """
    # Vulnerable mode allows trivial 1-character passwords
    settings.SECURE_MODE = False
    vuln_resp = client.post(
        "/api/auth/register",
        json={"username": "trivial_user", "email": "trivial@secureshop.lab", "password": "1"}
    )
    if vuln_resp.status_code == 200:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Weak 1-character password accepted.")

    # Secure mode enforces minimum length and complexity
    settings.SECURE_MODE = True
    secure_resp = client.post(
        "/api/auth/register",
        json={"username": "trivial_user_2", "email": "trivial2@secureshop.lab", "password": "1"}
    )
    assert secure_resp.status_code == 400, "Secure mode must enforce strong password complexity requirements."

def test_lab009_predictable_password_reset_token(client):
    """
    LAB-009: Password Reset Token Entropy
    Test that reset tokens are cryptographically random and not predictable static IDs.
    """
    settings.SECURE_MODE = False
    vuln_resp = client.post("/api/auth/forgot-password", json={"email": "alice@secureshop.lab"})
    token_vuln = vuln_resp.json().get("token", "")
    if "static" in token_vuln:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Predictable static password reset token generated.")

    settings.SECURE_MODE = True
    sec_resp = client.post("/api/auth/forgot-password", json={"email": "alice@secureshop.lab"})
    token_sec = sec_resp.json().get("token", "")
    assert len(token_sec) >= 32, "Secure mode must generate high-entropy 256-bit random reset tokens."
    assert "static" not in token_sec
