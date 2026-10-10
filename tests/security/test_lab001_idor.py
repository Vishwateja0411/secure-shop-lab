import pytest
from backend.app.config import settings

def test_lab001_idor_orders(client, auth_headers_alice, auth_headers_bob):
    """
    LAB-001: Broken Access Control (IDOR)
    Test that Alice cannot access Bob's order (#2).
    """
    # Test in Vulnerable Mode
    settings.SECURE_MODE = False
    vuln_resp = client.get("/api/orders/2", headers=auth_headers_alice)
    
    # In vulnerable mode, Alice can see Bob's order (200 OK) -> EXPECTED FAILURE — VULNERABLE LAB
    if vuln_resp.status_code == 200:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Alice successfully accessed Bob's order via IDOR.")

    # Test in Secure Mode
    settings.SECURE_MODE = True
    secure_resp = client.get("/api/orders/2", headers=auth_headers_alice)
    assert secure_resp.status_code == 403, "Secure mode must reject unauthorized access to Bob's order."

def test_lab001_idor_user_profile(client, auth_headers_alice):
    """
    LAB-001: Broken Object Level Authorization on User Profile
    Test that Alice cannot read Bob's private profile (user_id=3).
    """
    # Vulnerable mode
    settings.SECURE_MODE = False
    vuln_resp = client.get("/api/users/profile/3", headers=auth_headers_alice)
    if vuln_resp.status_code == 200:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Alice successfully read Bob's profile.")

    # Secure mode
    settings.SECURE_MODE = True
    secure_resp = client.get("/api/users/profile/3", headers=auth_headers_alice)
    assert secure_resp.status_code == 403, "Secure mode must restrict access to other users' profiles."
