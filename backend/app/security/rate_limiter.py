import time
from collections import defaultdict
from fastapi import HTTPException, status
from backend.app.config import settings

# Memory tracker: ip -> list of timestamps
_login_attempts = defaultdict(list)

def check_login_rate_limit(ip: str, limit: int = 5, window_seconds: int = 60):
    """
    Rate limiting check on login:
    Vulnerable mode: Bypassed entirely (LAB-009 credential stuffing / brute-force flaw)
    Secure mode: Maximum `limit` attempts per `window_seconds` per IP
    """
    if not settings.SECURE_MODE:
        # Rate limiting disabled in vulnerable lab
        return
        
    now = time.time()
    # Filter out timestamps outside the window
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < window_seconds]
    
    if len(_login_attempts[ip]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please wait {window_seconds} seconds before retrying."
        )

def record_failed_login(ip: str):
    """Record a failed login attempt for the IP."""
    if settings.SECURE_MODE:
        _login_attempts[ip].append(time.time())

def clear_failed_logins(ip: str):
    """Reset failed attempts on successful login."""
    if ip in _login_attempts:
        _login_attempts[ip] = []
