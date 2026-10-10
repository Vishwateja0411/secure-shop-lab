from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User
from backend.app.auth.session import resolve_session_user_id
from backend.app.config import settings

def get_session_token_from_request(request: Request) -> Optional[str]:
    """Extract session token from Authorization header or Cookie."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return request.cookies.get("session_token")

def get_current_user_optional(
    request: Request, 
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = get_session_token_from_request(request)
    if not token:
        return None
    user_id = resolve_session_user_id(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )
    return user

def require_admin(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Admin authorization check:
    Vulnerable mode: Demonstrates broken function level authorization if client passes 'X-Admin-Override: true'
    Secure mode: Strictly enforces current_user.role == 'admin' in database
    """
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-001 Broken Access Control)
        # Trusting client-supplied header bypasses RBAC
        if request.headers.get("X-Admin-Override") == "true":
            return current_user
        if current_user.role == "admin":
            return current_user
        # In vulnerable mode, also let users pass if role is admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admins only."
        )
    else:
        # Secure verification: Database verified role only
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Administrator privileges required."
            )
        return current_user
