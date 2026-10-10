import pytest
from backend.app.config import settings

def test_lab007_path_traversal(client, auth_headers_alice):
    """
    LAB-007: Path Traversal
    Test that directory traversal sequences ('../') are neutralized and cannot escape the storage directory.
    """
    traversal_path = "../../backend/app/config.py"

    # Vulnerable mode
    settings.SECURE_MODE = False
    vuln_resp = client.get(
        f"/api/orders/download/invoice?filename={traversal_path}",
        headers=auth_headers_alice
    )
    if vuln_resp.status_code == 200 and "SECRET_KEY" in vuln_resp.text:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Arbitrary file read succeeded via path traversal.")

    # Secure mode
    settings.SECURE_MODE = True
    secure_resp = client.get(
        f"/api/orders/download/invoice?filename={traversal_path}",
        headers=auth_headers_alice
    )
    # Secure mode strips path to 'config.py' and checks base directory, returning 404 or 403
    assert secure_resp.status_code in (403, 404), "Secure mode must prevent escaping the invoice directory."
    assert "SECRET_KEY" not in secure_resp.text
