import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException, status

# Allowlist of safe public mock catalog endpoints for Secure Mode
ALLOWED_TARGET_HOSTS = {"backend", "localhost", "127.0.0.1"}
ALLOWED_SECURE_PATHS = {"/api/mock-service/public-catalog"}

def is_internal_ip(ip_str: str) -> bool:
    """Check if an IP address belongs to loopback, private, or link-local ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False

def validate_ssrf_target(url: str, secure_mode: bool = False) -> str:
    """
    Validate target URL for SSRF protection:
    
    LAB RULE: The lab is self-contained. External internet requests are blocked by design.
    
    Vulnerable Mode:
      Allows requesting any internal service endpoint within the lab (e.g. mock secret vault).
      Demonstrates SSRF against internal microservices.
      
    Secure Mode:
      Strict allowlist: only explicitly permitted public catalog mock paths are allowed.
      Internal administrative endpoints and private IPs are blocked.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    
    if scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme. Only HTTP and HTTPS are permitted."
        )
        
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must contain a valid hostname."
        )

    # Educational Lab Boundary: only allow communication within the local lab containers
    if hostname not in ALLOWED_TARGET_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Educational Lab Rule: Out-of-boundary external scanning is prohibited. Use internal lab services (e.g., http://backend:8000/api/mock-service/...)."
        )

    if secure_mode:
        # Secure remediation: Strict path allowlisting
        # In secure mode, internal secret vault endpoints are blocked
        if parsed.path not in ALLOWED_SECURE_PATHS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SSRF Protection: Access to internal endpoint path is denied. Only allowlisted public catalog endpoints are accessible."
            )
            
    return url
