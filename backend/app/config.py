import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Lab Mode Toggle: false = vulnerable training lab, true = secure hardened mode
    SECURE_MODE: bool = False
    
    SECRET_KEY: str = "lab_insecure_default_secret_key_change_in_production_123456"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://secureshop:secureshop_password@postgres:5432/secureshop_db"
    )
    
    # Storage Paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"))
    INVOICE_DIR: str = os.getenv("INVOICE_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "invoices"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.INVOICE_DIR, exist_ok=True)
