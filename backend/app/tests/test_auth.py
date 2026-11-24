"""Tests for authentication endpoints."""
import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """Valid credentials return a JWT token."""
    from app.services.auth_service import AuthService
    from app.db.base import get_db_session
    from app.main import app
    async for db in app.dependency_overrides[get_db_session]():
        await AuthService(db).ensure_admin_exists()
        await db.commit()

    from app.core.config import get_settings
    s = get_settings()
    response = await client.post("/api/auth/login", json={"email": s.ADMIN_EMAIL, "password": s.ADMIN_PASSWORD})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Wrong password returns 401."""
    from app.core.config import get_settings
    s = get_settings()
    response = await client.post("/api/auth/login", json={"email": s.ADMIN_EMAIL, "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    """Unknown email returns 401 (not 404 — don't reveal user existence)."""
    response = await client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "pass"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    """Unauthenticated request to /api/auth/me returns 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(admin_client):
    """Authenticated admin can get their own profile."""
    response = await admin_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
