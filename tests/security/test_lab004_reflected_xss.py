import pytest
from backend.app.config import settings

def test_lab004_reflected_xss(client):
    """
    LAB-004: Reflected Cross-Site Scripting (XSS)
    Test that reflected input is escaped and does not reflect raw HTML tags.
    """
    payload = "<script>alert(1)</script>"

    # Vulnerable mode
    settings.SECURE_MODE = False
    vuln_resp = client.get(f"/api/products/search-echo?query={payload}")
    if vuln_resp.status_code == 200 and "<script>" in vuln_resp.json()["search_term"]:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Raw script payload reflected in response body.")

    # Secure mode
    settings.SECURE_MODE = True
    secure_resp = client.get(f"/api/products/search-echo?query={payload}")
    assert secure_resp.status_code == 200
    term = secure_resp.json()["search_term"]
    assert "<script>" not in term, "Secure mode must encode dangerous HTML characters."
    assert "&lt;script&gt;" in term
