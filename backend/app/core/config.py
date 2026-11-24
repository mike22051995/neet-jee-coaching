"""
Configuration module — application settings loaded from environment variables.

Layer: Core / Infrastructure
Why here: Centralising configuration in one place means every part of the app
imports from here rather than reading os.environ directly. Pydantic-Settings
validates and type-converts every value at startup, so a missing SECRET_KEY
crashes immediately with a clear error rather than silently at runtime.

Concept: Pydantic BaseSettings reads from environment variables (and .env files
if python-dotenv is installed). Fields with defaults are optional; fields without
defaults are required and will raise a ValidationError if absent.
"""

from functools import lru_cache
from typing import List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings in one place.

    'model_config' tells Pydantic to also load from a .env file in development.
    In production, real environment variables take precedence.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    # asyncpg driver for async SQLAlchemy: postgresql+asyncpg://user:pass@host/db
    DATABASE_URL: str

    # ── JWT Authentication ────────────────────────────────────────────────────
    # SECRET_KEY must be a long random string — never hardcode it.
    # Generate: python -c "import secrets; print(secrets.token_hex(64))"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Admin Bootstrap ───────────────────────────────────────────────────────
    # Used only once on first run to seed the initial admin account.
    ADMIN_EMAIL: str = "admin@coaching.in"
    ADMIN_PASSWORD: str = "ChangeMe123!"
    ADMIN_NAME: str = "Admin"

    # ── App ───────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    # ALLOWED_ORIGINS: comma-separated list of frontend origins for CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── File Upload ───────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 5

    # ── Test ──────────────────────────────────────────────────────────────────
    TEST_DATABASE_URL: str = ""

    @property
    def async_database_url(self) -> str:
        """
        Return the DATABASE_URL with the asyncpg driver prefix.

        Render (and many cloud providers) supply connection strings as
        'postgres://' or 'postgresql://' — SQLAlchemy's async engine requires
        'postgresql+asyncpg://'. This property normalises all three formats.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.

    @lru_cache ensures we read the environment only once at startup.
    FastAPI dependency injection calls this via Depends(get_settings).
    """
    return Settings()
