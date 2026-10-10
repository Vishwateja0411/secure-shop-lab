import httpx
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.models import User, Product, Order, AuditLog
from backend.app.auth.dependencies import require_admin
from backend.app.security.ssrf_validator import validate_ssrf_target
from backend.app.services.logger import log_security_event
from backend.app.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin & Security Dashboard"])

class ProductCreateRequest(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str] = "/uploads/default-product.png"

class SSRFImportRequest(BaseModel):
    webhook_url: str

class RoleUpdateRequest(BaseModel):
    role: str

class SecureModeToggleRequest(BaseModel):
    enable_secure_mode: bool

@router.get("/metrics")
def get_security_dashboard_metrics(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Security Dashboard KPI metrics:
    - User and order counts
    - Total logins and failed authentication events
    - Real-time SECURE_MODE status and vulnerability list
    """
    total_users = db.query(func.count(User.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    login_success_count = db.query(func.count(AuditLog.id)).filter(AuditLog.event_type == "AUTH_SUCCESS").scalar()
    login_failure_count = db.query(func.count(AuditLog.id)).filter(AuditLog.event_type == "AUTH_FAILURE").scalar()

    vulnerabilities = [
        {"id": "LAB-001", "name": "Broken Access Control (IDOR)", "category": "Authorization", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-002", "name": "SQL Injection (Product Search)", "category": "Injection", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-003", "name": "Stored Cross-Site Scripting (Reviews)", "category": "XSS", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-004", "name": "Reflected Cross-Site Scripting", "category": "XSS", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-005", "name": "Cross-Site Request Forgery (Email Update)", "category": "CSRF", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-006", "name": "Insecure File Upload (Avatar)", "category": "File Handling", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-007", "name": "Path Traversal (Invoice Download)", "category": "Path Traversal", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-008", "name": "Server-Side Request Forgery (Webhook / Catalog Import)", "category": "SSRF", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-009", "name": "Weak Authentication & Missing Rate Limit", "category": "Authentication", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-010", "name": "Insecure Session Management", "category": "Session Handling", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-011", "name": "Business Logic Flaw (Price / Quantity Manipulation)", "category": "Business Logic", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"},
        {"id": "LAB-012", "name": "Race Condition (Promo Credit Claim)", "category": "Concurrency", "status": "SECURED" if settings.SECURE_MODE else "VULNERABLE"}
    ]

    return {
        "lab_mode": "SECURE_MODE (HARDENED)" if settings.SECURE_MODE else "VULNERABLE TRAINING LAB",
        "secure_mode_enabled": settings.SECURE_MODE,
        "metrics": {
            "total_users": total_users,
            "total_orders": total_orders,
            "login_success_count": login_success_count,
            "login_failure_count": login_failure_count
        },
        "vulnerabilities": vulnerabilities
    }

@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, le=200),
    event_type: Optional[str] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve structured security audit logs."""
    q = db.query(AuditLog)
    if event_type:
        q = q.filter(AuditLog.event_type == event_type)
    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "event_type": l.event_type,
            "username": l.username,
            "ip_address": l.ip_address,
            "details": l.details,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]

@router.post("/import-webhook")
async def import_webhook_ssrf_lab(
    req: SSRFImportRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Simulated webhook / product feed import endpoint:
    Vulnerable mode: SSRF (LAB-008)
      - Accepts arbitrary local internal URL (e.g. http://backend:8000/api/mock-service/secret-vault)
    Secure mode:
      - Validates URL against strict allowlist (blocks internal secrets vault)
    """
    safe_url = validate_ssrf_target(req.webhook_url, secure_mode=settings.SECURE_MODE)

    log_security_event(
        event_type="SSRF_REQUEST",
        details=f"Admin {current_admin.username} initiated webhook fetch to {req.webhook_url}",
        username=current_admin.username,
        db=db
    )

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(safe_url)
            try:
                body = resp.json()
            except Exception:
                body = resp.text

            return {
                "status": "success",
                "target_url": safe_url,
                "http_status": resp.status_code,
                "response": body
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Webhook connection error: {str(e)}"
        )

@router.get("/users")
def list_all_users(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "balance": u.balance,
            "promo_claimed": u.promo_claimed,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]

@router.post("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    req: RoleUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    if req.role not in ("user", "admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be 'user' or 'admin'.")

    user.role = req.role
    db.commit()

    log_security_event(
        event_type="ADMIN_ACTION",
        details=f"Admin {current_admin.username} changed role for user {user.username} to {req.role}",
        username=current_admin.username,
        db=db
    )
    return {"status": "success", "message": f"User role updated to {req.role}"}

@router.post("/toggle-secure-mode")
def toggle_secure_mode(
    req: SecureModeToggleRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Dynamically toggle SECURE_MODE for interactive testing."""
    settings.SECURE_MODE = req.enable_secure_mode
    mode_str = "SECURE_MODE (HARDENED)" if settings.SECURE_MODE else "VULNERABLE TRAINING LAB"

    log_security_event(
        event_type="ADMIN_ACTION",
        details=f"Admin {current_admin.username} toggled lab mode to {mode_str}",
        username=current_admin.username,
        db=db
    )

    return {
        "status": "success",
        "secure_mode": settings.SECURE_MODE,
        "message": f"Lab mode switched to: {mode_str}"
    }

@router.post("/products")
def create_product(
    req: ProductCreateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    product = Product(
        name=req.name,
        description=req.description,
        price=req.price,
        stock=req.stock,
        category=req.category,
        image_url=req.image_url
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"status": "success", "product_id": product.id}

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    db.delete(product)
    db.commit()
    return {"status": "success", "message": "Product deleted"}
