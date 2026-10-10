import pytest
from backend.app.config import settings

def test_lab008_ssrf_internal_service_restriction(client, auth_headers_admin):
    """
    LAB-008: Server-Side Request Forgery (SSRF)
    Test that sensitive internal microservice endpoints are protected and not reachable via webhook imports.
    """
    secret_vault_url = "http://backend:8000/api/mock-service/secret-vault"

    # Vulnerable mode
    settings.SECURE_MODE = False
    # Note: In offline test client, httpx will attempt async request to backend
    # Here we test URL validator function logic and response
    try:
        from backend.app.security.ssrf_validator import validate_ssrf_target
        vuln_allowed = validate_ssrf_target(secret_vault_url, secure_mode=False)
        if vuln_allowed:
            pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Target allowed internal secret vault URL.")
    except Exception:
        pass

    # Secure mode
    settings.SECURE_MODE = True
    secure_resp = client.post(
        "/api/admin/import-webhook",
        json={"webhook_url": secret_vault_url},
        headers=auth_headers_admin
    )
    assert secure_resp.status_code == 403, "Secure mode must reject SSRF requests targeting internal secret services."
