"""
Security utilities — password hashing and JWT token creation/verification.

Layer: Core / Infrastructure
Why here: Security primitives (hashing, signing) are low-level utilities with
no business logic. Keeping them in `core` means services and routes can import
them without creating circular dependencies.

Concepts used:
- passlib CryptContext: wraps bcrypt so we never call bcrypt directly.
  bcrypt automatically salts passwords, so the same password produces different
  hashes each time — safe to store in the database.
- python-jose JWT: signs and verifies JSON Web Tokens. The token payload
  carries the user's id and role so the backend can authorise without
  a DB query on every request (stateless auth).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# CryptContext manages the hashing algorithm. Using bcrypt with 12 rounds.
# 'deprecated="auto"' means old hashes are upgraded silently on next login.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password with bcrypt.

    Never store plain-text passwords. This function is called once when
    an admin account is created or when a password is changed.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain-text attempt against the stored bcrypt hash.

    Returns True if they match, False otherwise. Uses constant-time
    comparison internally to prevent timing attacks.
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: The user's UUID (stored as 'sub' claim — standard JWT convention).
        role:    'admin' — included so route guards can check without a DB query.
        expires_delta: Override the default expiry from settings.

    The token is signed with SECRET_KEY using HMAC-SHA256.
    Anyone with the token can impersonate the user, so:
    - Use HTTPS in production (tokens in transit are encrypted).
    - Keep expiry short (default 60 minutes).
    - Invalidate tokens by rotating SECRET_KEY if a breach is suspected.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,       # subject = user UUID
        "role": role,         # checked by require_admin dependency
        "exp": expire,        # expiry — jose rejects expired tokens automatically
        "iat": datetime.now(timezone.utc),  # issued-at for auditing
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises JWTError if the token is expired, tampered with, or uses the
    wrong algorithm. The caller (auth dependency) converts this to HTTP 401.

    Returns the raw payload dict on success.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
