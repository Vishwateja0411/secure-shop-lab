import datetime
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import User, PasswordResetToken
from backend.app.auth.hashing import hash_password, verify_password, validate_password_strength
from backend.app.auth.session import create_session, invalidate_session, resolve_session_user_id
from backend.app.auth.dependencies import get_current_user, get_session_token_from_request
from backend.app.security.rate_limiter import check_login_rate_limit, record_failed_login, clear_failed_logins
from backend.app.services.logger import log_security_event
from backend.app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/register")
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    # 1. Validate password policy (LAB-009)
    valid, err_msg = validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Check username / email uniqueness
    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered.")

    new_user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        role="user",
        bio="Welcome to my profile!"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_security_event(
        event_type="USER_REGISTERED",
        details=f"New user registered: {new_user.username}",
        username=new_user.username,
        ip_address=request.client.host if request.client else "127.0.0.1",
        db=db
    )
    return {"status": "success", "message": "User registered successfully", "user_id": new_user.id}

@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Rate Limiting check (LAB-009 Missing Rate Limiting)
    check_login_rate_limit(client_ip)

    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        record_failed_login(client_ip)
        log_security_event(
            event_type="AUTH_FAILURE",
            details=f"Failed login attempt for username: {req.username}",
            username=req.username,
            ip_address=client_ip,
            db=db
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    clear_failed_logins(client_ip)
    
    # Session generation (LAB-010 Session Management)
    session_token = create_session(user.id, response)

    log_security_event(
        event_type="AUTH_SUCCESS",
        details=f"Successful login for user: {user.username} (role: {user.role})",
        username=user.username,
        ip_address=client_ip,
        db=db
    )

    return {
        "status": "success",
        "message": "Login successful",
        "token": session_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "balance": user.balance
        }
    }

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = get_session_token_from_request(request)
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    if token:
        user_id = resolve_session_user_id(token)
        user = db.query(User).filter(User.id == user_id).first() if user_id else None
        username = user.username if user else "unknown"
        invalidate_session(token, response)
        log_security_event(
            event_type="LOGOUT",
            details=f"User logged out: {username}",
            username=username,
            ip_address=client_ip,
            db=db
        )
    return {"status": "success", "message": "Logged out successfully"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url,
        "balance": current_user.balance,
        "promo_claimed": current_user.promo_claimed
    }

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # In secure mode, return generic response to prevent user enumeration
        return {"status": "success", "message": "If that email exists, a password reset link has been generated."}

    # Token generation:
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-009 Predictable Reset Token)
        # Predictable token constructed from user id and static string
        token_str = f"reset_{user.id}_static_12345"
    else:
        # Secure: Cryptographically random 32-byte hex token
        token_str = secrets.token_hex(32)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_str,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        used=False
    )
    db.add(reset_token)
    db.commit()

    log_security_event(
        event_type="PASSWORD_RESET_REQUESTED",
        details=f"Password reset token requested for user {user.username}",
        username=user.username,
        ip_address=request.client.host if request.client else "127.0.0.1",
        db=db
    )

    # In lab environment, return token in response for easy demonstration
    return {
        "status": "success",
        "message": "Password reset token generated.",
        "simulated_reset_link": f"/reset-password.html?token={token_str}",
        "token": token_str
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    valid, err_msg = validate_password_strength(req.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == req.token,
        PasswordResetToken.used == False
    ).first()

    if not token_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or already used reset token.")

    if datetime.datetime.utcnow() > token_record.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired.")

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.password_hash = hash_password(req.new_password)
    token_record.used = True
    db.commit()

    log_security_event(
        event_type="PASSWORD_RESET_COMPLETED",
        details=f"Password successfully reset for user {user.username}",
        username=user.username,
        ip_address=request.client.host if request.client else "127.0.0.1",
        db=db
    )
    return {"status": "success", "message": "Password updated successfully."}
