from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.app.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject security headers based on SECURE_MODE.
    Vulnerable mode: Weak/missing headers (vulnerable to clickjacking, MIME sniffing, XSS)
    Secure mode: Strict CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        if settings.SECURE_MODE:
            # Secure headers configuration
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "frame-ancestors 'none';"
            )
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            response.headers["X-XSS-Protection"] = "1; mode=block"
        else:
            # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (Security Misconfiguration)
            # Missing defensive headers allow clickjacking (framing), MIME-confusion attacks,
            # and unconstrained inline script execution.
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["X-Lab-Mode"] = "Vulnerable-Training-Lab"

        return response
