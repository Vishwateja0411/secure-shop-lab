import pytest
from backend.app.config import settings

def test_lab012_promo_double_claim_prevention(client, auth_headers_bob):
    """
    LAB-012: Race Condition / Concurrency Control
    Test that promo credits cannot be claimed twice by the same account.
    """
    settings.SECURE_MODE = True
    
    # First claim should succeed
    first_resp = client.post("/api/cart/claim-promo", json={"promo_code": "WELCOME50"}, headers=auth_headers_bob)
    assert first_resp.status_code == 200

    # Immediate second claim must be rejected
    second_resp = client.post("/api/cart/claim-promo", json={"promo_code": "WELCOME50"}, headers=auth_headers_bob)
    assert second_resp.status_code == 400, "Secure mode must reject second claim using atomic constraints."
