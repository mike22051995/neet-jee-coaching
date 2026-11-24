"""
Auth routes — login, logout, and /me.

Layer: API / Routes
All token lifecycle (issue, revoke) happens here via httpOnly cookies so the
JWT is never accessible to JavaScript, eliminating XSS token theft.

Rate limiting:
  Login is protected by slowapi: 5 attempts per 15 minutes per IP.
  The @limiter.limit decorator requires a Request parameter in the handler.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.limiter import limiter
from app.core.config import get_settings
from app.db.base import get_db_session
from app.models.user import User
from app.schemas.auth import AdminUserResponse, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

_COOKIE_NAME = "admin_token"


@router.post("/login")
@limiter.limit("5/15minutes")
async def login(
    request: Request,  # required by slowapi for IP-based limiting
    data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """
    Admin login — sets an httpOnly cookie on success.

    Returns 200 with {"message": "ok"} and a Set-Cookie header.
    The JWT is stored in an httpOnly cookie so JavaScript cannot read it,
    which prevents XSS-based token theft.

    Rate-limited to 5 attempts per 15 minutes per IP address.
    """
    service = AuthService(db)
    token_data = await service.authenticate(data.email, data.password)

    response = JSONResponse(content={"message": "ok"})
    # In production the frontend and backend are on different subdomains
    # (*.onrender.com), so the cookie needs SameSite=none + Secure=true to
    # travel cross-origin over HTTPS. In development (HTTP) lax is fine.
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token_data["access_token"],
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="none" if settings.is_production else "lax",
        secure=settings.is_production,
        path="/",
    )
    return response


@router.post("/logout")
async def logout() -> JSONResponse:
    """
    Clear the admin session cookie.

    Does not require authentication — a logged-out user hitting this is a no-op.
    """
    response = JSONResponse(content={"message": "logged out"})
    response.delete_cookie(key=_COOKIE_NAME, path="/", samesite="lax")
    return response


@router.get("/me", response_model=AdminUserResponse)
async def get_me(current_user: User = Depends(require_admin)) -> AdminUserResponse:
    """Return the currently authenticated admin's profile."""
    return AdminUserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
    )
