import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.database import get_db
from backend.app.models.models import User, Product, Order, OrderItem, Coupon
from backend.app.auth.dependencies import get_current_user
from backend.app.services.logger import log_security_event
from backend.app.config import settings

router = APIRouter(prefix="/api/cart", tags=["Cart & Checkout"])

class CartItemInput(BaseModel):
    product_id: int
    quantity: int
    client_price: Optional[float] = None  # Vulnerable client-controlled price field

class CheckoutRequest(BaseModel):
    items: List[CartItemInput]
    shipping_address: str
    coupon_code: Optional[str] = None

class PromoClaimRequest(BaseModel):
    promo_code: str = "WELCOME50"

@router.post("/checkout")
def checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Checkout endpoint:
    Vulnerable mode: Business Logic Flaws (LAB-011)
      - Allows negative quantities or client-specified prices.
      - Total amount can be manipulated to zero or negative values.
    Secure mode:
      - Validates quantity > 0.
      - Fetches official prices strictly from database records.
      - Verifies stock and user balance.
    """
    if not req.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty.")

    total_amount = 0.0
    order_items_to_create = []

    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-011 Business Logic Flaw)
        # 1. Accepts negative quantities without validation
        # 2. Honors client-supplied pricing if present
        for item in req.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found.")
            
            # Flaw: client can override price
            unit_price = item.client_price if item.client_price is not None else product.price
            subtotal = unit_price * item.quantity
            total_amount += subtotal

            order_items_to_create.append({
                "product_id": product.id,
                "product_name": product.name,
                "price": unit_price,
                "quantity": item.quantity
            })
    else:
        # Secure implementation:
        # 1. Strictly enforce quantity > 0 and stock availability
        # 2. Calculate prices entirely from server-side database
        for item in req.items:
            if item.quantity <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item quantity must be greater than zero.")
            
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found.")
            
            if product.stock < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient stock for {product.name}.")

            subtotal = product.price * item.quantity
            total_amount += subtotal

            order_items_to_create.append({
                "product_id": product.id,
                "product_name": product.name,
                "price": product.price,
                "quantity": item.quantity
            })

    # Apply coupon if provided
    discount_amount = 0.0
    if req.coupon_code:
        coupon = db.query(Coupon).filter(Coupon.code == req.coupon_code).first()
        if coupon:
            if not settings.SECURE_MODE:
                # Flaw: no usage count limit check
                discount_amount = total_amount * (coupon.discount_percent / 100.0)
            else:
                if coupon.times_used >= coupon.max_uses:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit reached.")
                discount_amount = total_amount * (coupon.discount_percent / 100.0)
                coupon.times_used += 1

    final_total = max(0.0, total_amount - discount_amount)

    # In secure mode, verify user has sufficient balance
    if settings.SECURE_MODE and current_user.balance < final_total:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient account balance to complete checkout.")

    # Deduct balance
    current_user.balance -= final_total

    # Create Order
    new_order = Order(
        user_id=current_user.id,
        total_amount=round(final_total, 2),
        status="completed",
        shipping_address=req.shipping_address
    )
    db.add(new_order)
    db.flush()

    for oi in order_items_to_create:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=oi["product_id"],
            product_name=oi["product_name"],
            price=oi["price"],
            quantity=oi["quantity"]
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)

    log_security_event(
        event_type="ORDER_CREATED",
        details=f"Order #{new_order.id} created by {current_user.username} for total ${new_order.total_amount}",
        username=current_user.username,
        db=db
    )

    return {
        "status": "success",
        "message": "Checkout completed successfully.",
        "order_id": new_order.id,
        "total_amount": new_order.total_amount,
        "remaining_balance": current_user.balance
    }

@router.post("/claim-promo")
async def claim_promo(
    req: PromoClaimRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Claim one-time $50 promotional credit:
    Vulnerable mode: Race Condition (LAB-012)
      - Non-atomic check-then-act with simulated asynchronous processing gap.
      - Concurrent requests can bypass check and claim credit multiple times.
    Secure mode:
      - Atomic database transaction with row locking or conditional update.
    """
    if req.promo_code != "WELCOME50":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid promo code.")

    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-012 Race Condition)
        # Check step
        if current_user.promo_claimed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promotion already claimed.")
        
        # Simulated async I/O or network delay creating a race window (TOCTOU)
        await asyncio.sleep(0.08)

        # Act step: state update happens without atomic lock
        current_user.promo_claimed = True
        current_user.balance += 50.0
        db.commit()
        
        return {
            "status": "success",
            "message": "Promo credit of $50 added to your account!",
            "new_balance": current_user.balance
        }
    else:
        # Secure implementation: Atomic SQL conditional update
        # Ensures only a single concurrent request can flip promo_claimed from False to True
        result = db.execute(
            text(
                "UPDATE users SET promo_claimed = TRUE, balance = balance + 50 "
                "WHERE id = :uid AND promo_claimed = FALSE"
            ),
            {"uid": current_user.id}
        )
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promotion already claimed."
            )

        db.refresh(current_user)
        return {
            "status": "success",
            "message": "Promo credit of $50 added to your account!",
            "new_balance": current_user.balance
        }
