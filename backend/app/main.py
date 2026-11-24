"""
FastAPI application entrypoint.

Layer: Application / Entry point
Why here: main.py wires together all the components (routers, middleware,
startup events) but contains no business logic itself.

Request lifecycle:
  Browser → nginx → uvicorn → FastAPI middleware stack →
  route handler → service → repository → DB → response

Startup events:
  On startup, the app ensures the admin account exists (bootstrap).
  Alembic migrations are run before this in docker-compose via:
    alembic upgrade head && uvicorn app.main:app ...
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.enrollment import router as enrollment_router
from app.api.routes.public import router as public_router
from app.core.config import get_settings
from app.db.base import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic using the new FastAPI lifespan context manager.

    On startup: ensure admin account exists (bootstrap).
    On shutdown: nothing special needed — connection pools close automatically.
    """
    logger.info("Starting NEET/JEE Coaching API — environment: %s", settings.ENVIRONMENT)

    # Bootstrap: create admin account if first run
    async with AsyncSessionLocal() as db:
        from app.services.auth_service import AuthService
        auth_service = AuthService(db)
        await auth_service.ensure_admin_exists()

    # Ensure upload directories exist
    for subdir in ["receipts", "public"]:
        path = os.path.join(settings.UPLOAD_DIR, subdir)
        os.makedirs(path, exist_ok=True)

    yield
    logger.info("API shutting down")


app = FastAPI(
    title="NEET/JEE Coaching API",
    description="Backend API for the NEET/JEE online coaching website",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,  # Disable Swagger in production
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow the React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount public uploads (logos, QR codes) as static files
# Receipts are NOT mounted here — they are served only via authenticated admin endpoints
uploads_public_dir = os.path.join(settings.UPLOAD_DIR, "public")
os.makedirs(uploads_public_dir, exist_ok=True)
app.mount("/uploads/public", StaticFiles(directory=uploads_public_dir), name="public_uploads")

# Register all routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(enrollment_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Simple health check used by Docker and load balancers."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}
