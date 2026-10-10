import io
import pytest
from backend.app.config import settings

def test_lab006_insecure_file_upload(client, auth_headers_alice):
    """
    LAB-006: Insecure File Upload
    Test that executable/HTML files are rejected and only safe image types are permitted.
    """
    fake_html_file = ("exploit.html", io.BytesIO(b"<h1>Defaced</h1>"), "text/html")

    # Vulnerable mode
    settings.SECURE_MODE = False
    vuln_resp = client.post(
        "/api/users/upload-avatar",
        files={"file": fake_html_file},
        headers=auth_headers_alice
    )
    if vuln_resp.status_code == 200 and "exploit.html" in vuln_resp.json().get("filename", ""):
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Unsanitized HTML file accepted as avatar.")

    # Secure mode
    settings.SECURE_MODE = True
    rejected_resp = client.post(
        "/api/users/upload-avatar",
        files={"file": ("malicious.php", io.BytesIO(b"<?php phpinfo(); ?>"), "application/x-php")},
        headers=auth_headers_alice
    )
    assert rejected_resp.status_code == 400, "Secure mode must reject non-image file extensions."

    # Valid PNG in secure mode
    valid_png = ("avatar.png", io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"), "image/png")
    valid_resp = client.post(
        "/api/users/upload-avatar",
        files={"file": valid_png},
        headers=auth_headers_alice
    )
    assert valid_resp.status_code == 200
    assert not valid_resp.json()["filename"].startswith("avatar.png"), "Secure mode must randomize uploaded filenames."
