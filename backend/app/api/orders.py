import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import Order, OrderItem, User
from backend.app.auth.dependencies import get_current_user
from backend.app.security.path_validator import resolve_safe_filepath
from backend.app.services.logger import log_security_event
from backend.app.config import settings

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("")
def list_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "total_amount": o.total_amount,
            "status": o.status,
            "shipping_address": o.shipping_address,
            "created_at": o.created_at.isoformat()
        }
        for o in orders
    ]

@router.get("/{order_id}")
def get_order_by_id(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get order details:
    Vulnerable mode: Broken Object Level Authorization / IDOR (LAB-001)
      - Returns order details for ANY user without checking ownership.
    Secure mode:
      - Validates current_user owns the order or is an administrator.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-001 IDOR)
        # Missing authorization check: Bob can view Alice's order
        pass
    else:
        # Secure implementation: Ownership verification
        if order.user_id != current_user.id and current_user.role != "admin":
            log_security_event(
                event_type="AUTHZ_FAILURE",
                details=f"Unauthorized IDOR attempt: user {current_user.username} tried accessing order #{order_id}",
                username=current_user.username,
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view this order."
            )

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "shipping_address": order.shipping_address,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product_name,
                "price": it.price,
                "quantity": it.quantity
            }
            for it in items
        ]
    }

@router.get("/download/invoice")
def download_invoice(
    filename: str = Query("invoice_sample.txt", description="Invoice file name"),
    current_user: User = Depends(get_current_user)
):
    """
    Download invoice document:
    Vulnerable mode: Path Traversal (LAB-007)
      - Directly opens path with user input, allowing '../../app/config.py' traversal.
    Secure mode:
      - Canonicalizes path and restricts reads strictly to the invoice directory.
    """
    # Ensure sample invoice exists
    sample_invoice = os.path.join(settings.INVOICE_DIR, "invoice_sample.txt")
    if not os.path.exists(sample_invoice):
        with open(sample_invoice, "w") as f:
            f.write("=== SECURESHOP OFFICIAL INVOICE ===\nOrder Reference: #1001\nStatus: Paid in Full\nThank you for shopping!\n")

    target_file = resolve_safe_filepath(settings.INVOICE_DIR, filename, secure_mode=settings.SECURE_MODE)

    if not os.path.exists(target_file):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice file not found.")

    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return PlainTextResponse(content=content, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read file: {str(e)}")
