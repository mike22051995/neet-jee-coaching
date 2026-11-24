"""
Test configuration and shared fixtures.

Concepts:
- pytest fixtures: reusable setup/teardown functions. Fixtures can depend on
  other fixtures (like get_test_db depends on the engine setup).
- pytest-asyncio: runs async test functions in an event loop.
- AsyncClient from httpx: makes real HTTP requests to the FastAPI app in tests
  without starting a real server (uses ASGI transport).
- Test database: we use a separate DB (TEST_DATABASE_URL) so tests never
  touch the development database. Each test gets a fresh set of tables via
  create_all / drop_all.
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base, get_db_session
from app.main import app

settings = get_settings()

TEST_DB_URL = settings.TEST_DATABASE_URL or settings.DATABASE_URL.replace(
    settings.DATABASE_URL.rsplit("/", 1)[-1], "neetjee_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Share a single event loop across all tests in the session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create the test DB engine once per session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Provide a fresh DB session per test, rolled back after each test.

    Rolling back instead of truncating is faster and ensures test isolation
    without leaving data behind.
    """
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """
    HTTP test client that uses the test DB session.

    We override the get_db_session dependency so the app uses our test session
    instead of creating a new production one.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client):
    """
    Create an admin user and return a valid JWT token.
    Used by tests that need to call admin-protected endpoints.
    """
    from app.core.security import hash_password
    from app.models.user import User

    # We need to create the admin directly in the DB for the fixture
    # (we can't use the login endpoint before the user exists)
    # This fixture is intentionally simple — real admin creation tested in auth tests.
    response = await client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,
    })
    if response.status_code == 401:
        # Bootstrap the admin first
        from app.services.auth_service import AuthService
        # Get the db session from the dependency override
        async for db in app.dependency_overrides[get_db_session]():
            service = AuthService(db)
            await service.ensure_admin_exists()
            await db.commit()
        response = await client.post("/api/auth/login", json={
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
        })

    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_client(client, admin_token):
    """HTTP client with admin Authorization header pre-set."""
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client
