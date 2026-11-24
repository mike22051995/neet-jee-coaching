"""
Authentication service — login and admin account management.

Layer: Service
Why here: Business logic for authentication (rate-limit tracking, login
validation, token generation) belongs in the service layer, not in the
route handler. The route just calls service methods and returns HTTP responses.

This service is responsible for:
- Validating credentials (email + password)
- Generating JWT tokens
- Creating the initial admin account from environment variables

It does NOT handle:
- HTTP request/response format (that's the route's job)
- Password hashing algorithm details (that's core/security.py)
- DB session lifecycle (that's the dependency/DB layer)
"""

import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """
    Handles all authentication operations.

    Constructor takes the DB session so it can be injected via FastAPI's
    dependency injection system. The route creates the service like:
        service = AuthService(db)
    This avoids global state and makes the service easy to test.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def authenticate(self, email: str, password: str) -> dict:
        """
        Validate credentials and return a JWT token dict.

        Flow:
        1. Look up the user by email.
        2. Verify the password against the stored bcrypt hash.
        3. Create and return a JWT access token.

        Security note: We always call verify_password even if the user is not
        found. This takes the same time as a real password check and prevents
        timing attacks that could reveal which email addresses exist.

        Raises HTTP 401 if credentials are wrong (deliberately vague message
        — don't reveal whether the email exists).
        """
        # Step 1: find user
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()

        # Step 2: verify password (always run, even if user not found)
        dummy_hash = hash_password("dummy") if user is None else user.hashed_password
        password_ok = verify_password(password, dummy_hash if user is None else user.hashed_password)

        if user is None or not password_ok or not user.is_active:
            logger.warning("Failed login attempt for email: %s", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Step 3: create token
        token = create_access_token(
            subject=str(user.id),
            role=user.role,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        logger.info("Admin login successful: %s", user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def ensure_admin_exists(self) -> None:
        """
        Bootstrap: create the initial admin account if none exists.

        Called once at application startup. Uses ADMIN_EMAIL / ADMIN_PASSWORD
        from the .env file. If an admin already exists, this is a no-op.

        This is the ONLY way to create admin accounts. There is no public
        "register admin" endpoint — that would be a security vulnerability.
        """
        result = await self.db.execute(select(User).limit(1))
        existing = result.scalar_one_or_none()
        if existing is not None:
            return

        admin = User(
            email=settings.ADMIN_EMAIL.lower(),
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            name=settings.ADMIN_NAME,
            role="admin",
            is_active=True,
        )
        self.db.add(admin)
        await self.db.commit()
        logger.info("Admin account created: %s", settings.ADMIN_EMAIL)
