import pytest
from backend.app.config import settings

def test_lab011_negative_quantity_manipulation(client, auth_headers_alice):
    """
    LAB-011: Business Logic Flaws
    Test that negative item quantities and client price overrides are rejected.
    """
    tampered_cart = [
        {"product_id": 1, "quantity": -5, "client_price": None}
    ]

    # Vulnerable mode allows negative quantities
    settings.SECURE_MODE = False
    vuln_resp = client.post(
        "/api/cart/checkout",
        json={"items": tampered_cart, "shipping_address": "Test Lab Street"},
        headers=auth_headers_alice
    )
    if vuln_resp.status_code == 200:
        pytest.xfail("EXPECTED FAILURE — VULNERABLE LAB: Checkout accepted negative item quantity.")

    # Secure mode strictly requires quantity > 0
    settings.SECURE_MODE = True
    secure_resp = client.post(
        "/api/cart/checkout",
        json={"items": tampered_cart, "shipping_address": "Test Lab Street"},
        headers=auth_headers_alice
    )
    assert secure_resp.status_code == 400, "Secure mode must reject non-positive quantities."
