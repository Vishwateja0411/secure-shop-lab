import hashlib
from passlib.context import CryptContext
from backend.app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash password according to mode:
    Vulnerable mode: Uses plain MD5 without salt (LAB-009)
    Secure mode: Uses salted Bcrypt with strong cost factor
    """
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-009)
        # MD5 is obsolete, collision-prone, and trivially crackable via rainbow tables
        return hashlib.md5(password.encode("utf-8")).hexdigest()
    else:
        # Secure implementation: Salted Bcrypt
        return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password based on hash type."""
    if not settings.SECURE_MODE:
        # Vulnerable mode check
        md5_hash = hashlib.md5(plain_password.encode("utf-8")).hexdigest()
        if md5_hash == hashed_password:
            return True
        # Allow checking against bcrypt if seeded with bcrypt
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    else:
        # Secure mode check
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Fallback for lab users transitioning to secure mode
            return hashlib.md5(plain_password.encode("utf-8")).hexdigest() == hashed_password

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Password policy check:
    Vulnerable mode: Accepts any password of length >= 1
    Secure mode: Requires minimum 8 characters, uppercase, lowercase, number, and special character
    """
    if not settings.SECURE_MODE:
        if len(password) < 1:
            return False, "Password cannot be empty"
        return True, ""
    
    # Secure policy validation
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character."
    
    return True, ""
