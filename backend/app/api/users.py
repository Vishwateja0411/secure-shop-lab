import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Header, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import User
from backend.app.auth.dependencies import get_current_user
from backend.app.services.logger import log_security_event
from backend.app.config import settings

router = APIRouter(prefix="/api/users", tags=["Users"])

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

class ProfileUpdateRequest(BaseModel):
    bio: Optional[str] = None

@router.get("/profile/{user_id}")
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user profile:
    Vulnerable mode: Broken Object Level Authorization (LAB-001)
      - Returns private profile data of any user without authorization.
    Secure mode:
      - Restricts viewing private profile info to the owner or an administrator.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-001 IDOR)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "balance": user.balance
        }
    else:
        # Secure implementation: Check ownership
        if current_user.id != user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access profile data of other users."
            )
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "balance": user.balance
        }

@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar:
    Vulnerable mode: Insecure File Upload (LAB-006)
      - Uses raw original filename, allowing directory escape or executable extensions (.html, .php, .sh).
      - No MIME type validation or size limit.
    Secure mode:
      - Validates extension against whitelist (.png, .jpg, .jpeg, .webp).
      - Checks Content-Type and file size <= 2MB.
      - Generates random UUID filename to prevent overwrites and directory traversal.
    """
    content = await file.read()

    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-006 Insecure File Upload)
        # 1. Unsanitized original filename preserved
        # 2. No file extension whitelist
        # 3. No file size check
        saved_filename = file.filename
        file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        avatar_url = f"/uploads/{saved_filename}"
        current_user.avatar_url = avatar_url
        db.commit()

        log_security_event(
            event_type="FILE_UPLOAD",
            details=f"Insecure file upload completed: {saved_filename} ({len(content)} bytes)",
            username=current_user.username,
            db=db
        )

        return {
            "status": "success",
            "message": "Avatar uploaded (Vulnerable mode: raw filename preserved)",
            "avatar_url": avatar_url,
            "filename": saved_filename
        }
    else:
        # Secure implementation:
        # 1. Size check
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds maximum 2MB limit.")

        # 2. Extension validation
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file extension. Allowed: {list(ALLOWED_IMAGE_EXTENSIONS)}")

        # 3. MIME type check
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file MIME type.")

        # 4. Randomized filename to prevent overwriting and traversal
        safe_filename = f"avatar_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        avatar_url = f"/uploads/{safe_filename}"
        current_user.avatar_url = avatar_url
        db.commit()

        log_security_event(
            event_type="FILE_UPLOAD",
            details=f"Secure avatar uploaded: {safe_filename} ({len(content)} bytes)",
            username=current_user.username,
            db=db
        )

        return {
            "status": "success",
            "message": "Avatar uploaded securely",
            "avatar_url": avatar_url,
            "filename": safe_filename
        }

@router.post("/csrf-change-email")
def change_email_csrf_demo(
    email: EmailStr = Form(...),
    request: Request = None,
    x_csrf_token: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user email endpoint:
    Vulnerable mode: Cross-Site Request Forgery (LAB-005)
      - Accepts state-changing POST requests using ambient cookie auth without anti-CSRF token.
    Secure mode:
      - Validates presence of anti-CSRF token header 'X-CSRF-Token'.
    """
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-005 CSRF)
        # Missing anti-CSRF validation enables cross-origin form attacks
        current_user.email = email
        db.commit()
        return {"status": "success", "message": f"Email successfully updated to {email} (Vulnerable: No CSRF verification)"}
    else:
        # Secure implementation: Anti-CSRF token validation
        # Expects matching token in header
        if not x_csrf_token or len(x_csrf_token) < 16:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF verification failed: Missing or invalid X-CSRF-Token header."
            )
        current_user.email = email
        db.commit()
        return {"status": "success", "message": f"Email successfully updated to {email} (Secure: CSRF token verified)"}
