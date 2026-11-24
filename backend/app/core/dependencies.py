"""
FastAPI dependency functions for authentication and authorisation.

Layer: Core / API
Why here: Dependencies are reusable functions injected into route handlers
via FastAPI's Depends() system. Keeping them in `core` means any router
can import them without importing from sibling modules.

How FastAPI dependency injection works:
  When FastAPI processes a request, it calls each Depends() function and
  passes the result to the route handler. If a dependency raises HTTPException,
  FastAPI returns the error response immediately without calling the handler.

Authentication flow (cookie-based):
  1. Client's browser sends the httpOnly 'admin_token' cookie automatically.
  2. get_current_user() reads the cookie, decodes and verifies the JWT.
  3. require_admin() additionally checks that role == "admin".
  4. Route handler receives the User object — it never touches the JWT directly.

  Using httpOnly cookies instead of Authorization headers means the token is
  never readable by JavaScript, which prevents XSS-based token theft.
"""

import logging
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.base import get_db_session
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_current_user(
    admin_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Dependency: read the httpOnly 'admin_token' cookie and return the User.

    FastAPI injects the cookie value automatically from the incoming request.
    If the cookie is absent, expired, or tampered with, raises HTTP 401.

    Raises HTTP 401 if:
    - Cookie is absent
    - Token is expired or tampered
    - User not found in DB (account deleted after token was issued)
    - User account is inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if not admin_token:
        raise credentials_exception

    try:
        payload = decode_access_token(admin_token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise credentials_exception from exc

    # Verify the user still exists and is active so that deactivating an admin
    # account takes effect on the next request rather than waiting for expiry.
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency: require the authenticated user to have role='admin'.

    Use this on every admin-only route to ensure non-admin tokens are rejected
    at the API boundary, not just in frontend routing.

    Raises HTTP 403 if the user's role is not 'admin'.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
