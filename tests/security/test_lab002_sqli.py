import pytest
from backend.app.config import settings

def test_lab002_sql_injection_search(client):
    """
    LAB-002: SQL Injection
    Test that input containing SQL syntax is properly parameterized and not executed dynamically.
    """
    injection_payload = "' OR '1'='1"

    # Test in Vulnerable Mode
    settings.SECURE_MODE = False
    vuln_resp = client.get(f"/api/products/search?q={injection_payload}")
    
    # In vulnerable mode, ' OR '1'='1 returns all products regardless of name
    if vuln_resp.status_code == 200 and len(vuln_resp.json()) >= 6:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Raw SQL concatenation executed injection payload.")

    # Test in Secure Mode
    settings.SECURE_MODE = True
    secure_resp = client.get(f"/api/products/search?q={injection_payload}")
    assert secure_resp.status_code == 200
    # Parameterized query searches for literal string "' OR '1'='1", which returns 0 matches
    assert len(secure_resp.json()) == 0, "Secure mode must treat SQL metacharacters as literal query string."
