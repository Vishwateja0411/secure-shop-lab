import time
import secrets
import base64
import json
from typing import Optional, Dict
from fastapi import Response
from backend.app.config import settings

# In-memory session store (mapping token -> dict with user_id, expires_at)
SESSION_STORE: Dict[str, dict] = {}

def create_session(user_id: int, response: Response) -> str:
    """
    Generate session token and set cookie:
    Vulnerable mode: Predictable token, no HttpOnly flag, no expiration enforcement (LAB-010)
    Secure mode: 256-bit cryptographic token, server-side TTL, HttpOnly and SameSite=Lax
    """
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-010)
        # Predictable format: base64 encoded user_id + timestamp, trivial to forge
        token_payload = json.dumps({"uid": user_id, "mode": "insecure_lab"})
        token = "sess_" + base64.b64encode(token_payload.encode()).decode()
        
        # Insecure cookie settings: accessible to JavaScript (enabling Stored XSS session theft)
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=False,  # Vulnerable: JS can read document.cookie
            samesite="none",
            secure=False
        )
        SESSION_STORE[token] = {"user_id": user_id, "expires_at": time.time() + 86400}
        return token
    else:
        # Secure implementation: 32 bytes cryptographically secure random token
        token = secrets.token_urlsafe(32)
        ttl = 3600  # 1 hour
        SESSION_STORE[token] = {
            "user_id": user_id,
            "expires_at": time.time() + ttl
        }
        
        # Hardened cookie flags: HttpOnly prevents XSS token extraction, SameSite mitigates CSRF
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,  # Set to True in production HTTPS
            max_age=ttl
        )
        return token

def resolve_session_user_id(token: str) -> Optional[int]:
    """Retrieve user_id from session token."""
    if not token:
        return None
        
    if not settings.SECURE_MODE:
        # Check predictable token format
        if token.startswith("sess_"):
            try:
                raw = base64.b64decode(token[5:]).decode()
                payload = json.loads(raw)
                return int(payload.get("uid"))
            except Exception:
                pass
        # Also check store
        if token in SESSION_STORE:
            return SESSION_STORE[token]["user_id"]
        return None
    else:
        # Secure lookup with expiry validation
        entry = SESSION_STORE.get(token)
        if not entry:
            return None
        if time.time() > entry.get("expires_at", 0):
            # Session expired
            SESSION_STORE.pop(token, None)
            return None
        return entry.get("user_id")

def invalidate_session(token: str, response: Response):
    """Revoke session on logout."""
    if token in SESSION_STORE:
        SESSION_STORE.pop(token, None)
    response.delete_cookie(key="session_token")
