import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.services.seed import seed_database
from backend.app.security.headers import SecurityHeadersMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.products import router as products_router
from backend.app.api.cart import router as cart_router
from backend.app.api.orders import router as orders_router
from backend.app.api.users import router as users_router
from backend.app.api.admin import router as admin_router
from backend.app.api.mock_service import router as mock_service_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed database and ensure directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.INVOICE_DIR, exist_ok=True)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="SecureShop Lab API",
    description="Intentionally vulnerable e-commerce web application lab for application security and secure coding training.",
    version="1.0.0",
    lifespan=lifespan
)

# Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration
if not settings.SECURE_MODE:
    # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (CORS Misconfiguration)
    # Wildcard origin with credentials allowed creates cross-origin leakage vulnerabilities
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Hardened CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:80", "http://127.0.0.1:80"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )

# Static file serving for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(mock_service_router)

# Custom Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE (Verbose Error Handling / Information Disclosure)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "path": request.url.path
            }
        )
    else:
        # Hardened generic error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please contact the administrator."
            }
        )

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "SecureShop Lab",
        "secure_mode": settings.SECURE_MODE,
        "mode_label": "SECURE_MODE" if settings.SECURE_MODE else "VULNERABLE_LAB"
    }

# Mount frontend static files for direct host execution (fallback when running outside Nginx/Docker)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

