import logging
import json
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.models import AuditLog

# Setup python logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("secureshop.security")

SENSITIVE_KEYS = {"password", "secret", "token", "authorization", "cookie", "card", "cvv"}

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive keys from log payloads."""
    sanitized = {}
    for k, v in data.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_data(v)
        else:
            sanitized[k] = v
    return sanitized

def log_security_event(
    event_type: str,
    details: str,
    username: Optional[str] = None,
    ip_address: Optional[str] = "127.0.0.1",
    extra: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
):
    """
    Log a security event with structured output and database persistence for the Security Dashboard.
    Ensures passwords, tokens, and secrets are NEVER logged.
    """
    cleaned_extra = sanitize_data(extra) if extra else {}
    
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "username": username or "anonymous",
        "ip_address": ip_address,
        "details": details,
        "metadata": cleaned_extra
    }
    
    # Emit structured console log
    logger.info(json.dumps(log_entry))

    # Persist in audit database if session provided
    if db:
        try:
            audit = AuditLog(
                event_type=event_type,
                username=username,
                ip_address=ip_address,
                details=f"{details} | Meta: {json.dumps(cleaned_extra)}" if cleaned_extra else details
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to record audit log in DB: {e}")
            db.rollback()
