import os
from sqlalchemy.orm import Session
from backend.app.database import engine, Base
from backend.app.models.models import User, Product, Review, Order, OrderItem, Coupon, AuditLog
from backend.app.auth.hashing import hash_password
from backend.app.config import settings

def seed_database(db: Session):
    """Seed database with realistic initial training data."""
    Base.metadata.create_all(bind=engine)

    # 1. Ensure sample invoice file exists
    os.makedirs(settings.INVOICE_DIR, exist_ok=True)
    sample_invoice_path = os.path.join(settings.INVOICE_DIR, "invoice_sample.txt")
    if not os.path.exists(sample_invoice_path):
        with open(sample_invoice_path, "w", encoding="utf-8") as f:
            f.write(
                "=====================================================\n"
                "           SECURESHOP LAB OFFICIAL INVOICE           \n"
                "=====================================================\n"
                "Order ID: 1001\n"
                "Customer: Alice Smith (alice@secureshop.lab)\n"
                "Date: 2026-10-10\n"
                "Items:\n"
                "  1x Hardware Security Key FIDO2 - $49.99\n"
                "  1x Faraday Shield Sleeve - $19.99\n"
                "Total: $69.98 USD\n"
                "Status: PAID IN FULL\n"
                "=====================================================\n"
            )

    # 2. Check if users already seeded
    if db.query(User).first():
        return

    # Create default demo accounts
    admin = User(
        username="admin",
        email="admin@secureshop.lab",
        password_hash=hash_password("AdminPass123!"),
        role="admin",
        bio="Lead Security Architect & Administrator.",
        avatar_url="/uploads/default-admin.png",
        balance=500.0
    )
    alice = User(
        username="alice",
        email="alice@secureshop.lab",
        password_hash=hash_password("AlicePass123!"),
        role="user",
        bio="Application Security Engineer studying defense.",
        avatar_url="/uploads/default-avatar.png",
        balance=150.0
    )
    bob = User(
        username="bob",
        email="bob@secureshop.lab",
        password_hash=hash_password("BobPass123!"),
        role="user",
        bio="QA Engineer learning penetration testing.",
        avatar_url="/uploads/default-avatar.png",
        balance=100.0
    )
    db.add_all([admin, alice, bob])
    db.commit()
    db.refresh(admin)
    db.refresh(alice)
    db.refresh(bob)

    # Seed Products
    products = [
        Product(
            name="Hardware Security Key NFC",
            description="FIDO2, U2F, and WebAuthn certified security key for phishing-resistant MFA.",
            price=49.99,
            stock=120,
            category="Hardware",
            image_url="/uploads/product_key.png"
        ),
        Product(
            name="Faraday Signal Blocking Bag",
            description="Military-grade RF shielding pouch blocking GPS, RFID, WiFi, and Bluetooth signals.",
            price=24.50,
            stock=85,
            category="Accessories",
            image_url="/uploads/product_faraday.png"
        ),
        Product(
            name="Hardware Hacking Multi-Tool Kit",
            description="Pocket bus analyzer, logic probe, UART/SPI bridge, and JTAG debugging module.",
            price=89.00,
            stock=40,
            category="Tools",
            image_url="/uploads/product_multitool.png"
        ),
        Product(
            name="Encrypted USB 3.2 Drive 64GB",
            description="Hardware-encrypted storage device with onboard alphanumeric keypad PIN unlock.",
            price=79.99,
            stock=60,
            category="Hardware",
            image_url="/uploads/product_usb.png"
        ),
        Product(
            name="Software Vulnerability Analysis Handbook",
            description="Comprehensive guide to source code review, threat modeling, and defensive engineering.",
            price=39.95,
            stock=150,
            category="Books",
            image_url="/uploads/product_book.png"
        ),
        Product(
            name="Software Defined Radio (SDR) Receiver",
            description="RTL2832U & R820T2 wideband software radio dongle with high-precision TCXO.",
            price=34.90,
            stock=70,
            category="Tools",
            image_url="/uploads/product_sdr.png"
        )
    ]
    db.add_all(products)
    db.commit()
    for p in products:
        db.refresh(p)

    # Seed Coupons
    c1 = Coupon(code="SAVE20", discount_percent=20.0, max_uses=100, times_used=0)
    c2 = Coupon(code="FLASH50", discount_percent=50.0, max_uses=1, times_used=0)
    c3 = Coupon(code="VIP10", discount_percent=10.0, max_uses=500, times_used=0)
    db.add_all([c1, c2, c3])
    db.commit()

    # Seed Sample Orders (Alice and Bob)
    order_alice = Order(
        user_id=alice.id,
        total_amount=74.49,
        status="completed",
        shipping_address="123 Defense Way, Suite 400, Cyber City"
    )
    db.add(order_alice)
    db.commit()
    db.refresh(order_alice)

    item1 = OrderItem(order_id=order_alice.id, product_id=products[0].id, product_name=products[0].name, price=products[0].price, quantity=1)
    item2 = OrderItem(order_id=order_alice.id, product_id=products[1].id, product_name=products[1].name, price=products[1].price, quantity=1)
    db.add_all([item1, item2])

    order_bob = Order(
        user_id=bob.id,
        total_amount=89.00,
        status="completed",
        shipping_address="456 Infiltration Blvd, Apt 9, Sector 7"
    )
    db.add(order_bob)
    db.commit()
    db.refresh(order_bob)

    item3 = OrderItem(order_id=order_bob.id, product_id=products[2].id, product_name=products[2].name, price=products[2].price, quantity=1)
    db.add(item3)

    # Seed Sample Reviews
    rev1 = Review(
        product_id=products[0].id,
        user_id=alice.id,
        username="alice",
        rating=5,
        comment="Essential security tool for web accounts. Seamless FIDO2 WebAuthn authentication."
    )
    rev2 = Review(
        product_id=products[0].id,
        user_id=bob.id,
        username="bob",
        rating=4,
        comment="Works great with all my services. Build quality feels very sturdy."
    )
    db.add_all([rev1, rev2])

    # Seed initial audit log entries
    log1 = AuditLog(
        event_type="SYSTEM_BOOT",
        username="system",
        ip_address="127.0.0.1",
        details="SecureShop Lab environment initialized with default seed data."
    )
    log2 = AuditLog(
        event_type="AUTH_SUCCESS",
        username="alice",
        ip_address="127.0.0.1",
        details="Initial demo login for alice."
    )
    db.add_all([log1, log2])

    db.commit()
