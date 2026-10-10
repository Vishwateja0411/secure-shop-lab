from fastapi import APIRouter

router = APIRouter(prefix="/api/mock-service", tags=["Local Mock Services"])

@router.get("/public-catalog")
def mock_public_catalog():
    """Simulated public third-party product feed (Permitted in Secure Mode)."""
    return {
        "status": "online",
        "service": "Public Supplier Catalog",
        "items": [
            {"sku": "SUP-101", "name": "USB Rubber Ducky Case", "price": 14.99},
            {"sku": "SUP-102", "name": "RFID Blocking Sleeve", "price": 8.50}
        ]
    }

@router.get("/internal-inventory")
def mock_internal_inventory():
    """Simulated internal warehouse microservice."""
    return {
        "status": "internal_only",
        "service": "Warehouse Inventory Management",
        "warehouse_location": "Building 4B",
        "reserved_units": 450,
        "internal_api_version": "v1.4"
    }

@router.get("/secret-vault")
def mock_secret_vault():
    """
    Simulated internal secrets vault service:
    In vulnerable mode, accessible via SSRF (LAB-008) by requesting http://backend:8000/api/mock-service/secret-vault.
    In secure mode, blocked by SSRF allowlisting.
    """
    return {
        "status": "RESTRICTED",
        "classification": "TOP_SECRET_INTERNAL",
        "service": "Internal Credential & Key Vault",
        "vault_secret": "LAB_INTERNAL_MICROSERVICE_KEY_9941_DEMO",
        "admin_access_ip": "127.0.0.1"
    }
