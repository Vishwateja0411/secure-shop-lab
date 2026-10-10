import pytest
from backend.app.config import settings

def test_lab003_stored_xss_review(client, auth_headers_alice):
    """
    LAB-003: Stored Cross-Site Scripting (XSS)
    Test that user submitted review comments are sanitized/escaped before persistence.
    """
    xss_payload = "<img src=x onerror=alert('xss')>"

    # Vulnerable mode
    settings.SECURE_MODE = False
    vuln_resp = client.post(
        "/api/products/1/reviews",
        json={"rating": 5, "comment": xss_payload},
        headers=auth_headers_alice
    )
    if vuln_resp.status_code == 200 and vuln_resp.json()["review"]["comment"] == xss_payload:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Stored XSS payload persisted unescaped.")

    # Secure mode
    settings.SECURE_MODE = True
    secure_resp = client.post(
        "/api/products/1/reviews",
        json={"rating": 5, "comment": xss_payload},
        headers=auth_headers_alice
    )
    assert secure_resp.status_code == 200
    saved_comment = secure_resp.json()["review"]["comment"]
    assert "<img" not in saved_comment, "Secure mode must entity-encode HTML tags."
    assert "&lt;img" in saved_comment or "&gt;" in saved_comment
