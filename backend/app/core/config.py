import os
from typing import List

class Settings:
    PROJECT_NAME: str = "Guru Yuktha — Academic Navigation & Tracking System"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "guruyuktha_secret_key_super_secure_2026_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database: Supports SQLite (local) and PostgreSQL (production).
    # Normalizes postgres:// to postgresql:// if needed for SQLAlchemy 2.0.
    raw_db_url: str = os.getenv("DATABASE_URL", "sqlite:///./guruyuktha.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = raw_db_url
    
    # Seeding control: default false for production safety
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "false").strip().lower() in ("true", "1", "t", "yes")
    
    # CORS Origins (comma-separated list of origins)
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Uploads
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
