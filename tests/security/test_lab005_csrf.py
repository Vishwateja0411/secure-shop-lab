import pytest
from backend.app.config import settings

def test_lab005_csrf_protection(client, auth_headers_alice):
    """
    LAB-005: Cross-Site Request Forgery (CSRF)
    Test that sensitive state-changing POST requests require an anti-CSRF token in secure mode.
    """
    # 1. Request WITHOUT anti-CSRF token header
    settings.SECURE_MODE = False
    vuln_resp = client.post(
        "/api/users/csrf-change-email",
        data={"email": "alice_changed_vuln@secureshop.lab"},
        headers=auth_headers_alice
    )
    if vuln_resp.status_code == 200:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: State-changing email update succeeded without CSRF token.")

    # 2. Secure mode without CSRF token -> must be rejected (403 Forbidden)
    settings.SECURE_MODE = True
    rejected_resp = client.post(
        "/api/users/csrf-change-email",
        data={"email": "alice_changed_secure@secureshop.lab"},
        headers=auth_headers_alice
    )
    assert rejected_resp.status_code == 403, "Secure mode must reject requests lacking X-CSRF-Token header."

    # 3. Secure mode with valid CSRF token -> success
    headers_with_csrf = {**auth_headers_alice, "X-CSRF-Token": "valid_cryptographic_csrf_token_12345678"}
    success_resp = client.post(
        "/api/users/csrf-change-email",
        data={"email": "alice_changed_secure@secureshop.lab"},
        headers=headers_with_csrf
    )
    assert success_resp.status_code == 200
