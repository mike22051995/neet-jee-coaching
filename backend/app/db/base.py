"""
Database session factory and declarative base.

Layer: DB / Infrastructure
Why here: All SQLAlchemy setup lives in one module. Services and repositories
import `get_db_session` as a FastAPI dependency — they never create sessions
themselves. This ensures every request gets its own session and that sessions
are properly closed, even when an exception occurs.

Concepts:
- AsyncEngine: SQLAlchemy's async engine wraps asyncpg to run queries without
  blocking the event loop — essential for FastAPI's async request handling.
- AsyncSession: One session per HTTP request. A session tracks all ORM objects
  touched in a request and flushes changes to the DB atomically.
- async_sessionmaker: Factory that creates new AsyncSession instances.
- DeclarativeBase: Every ORM model inherits from this — it registers the model
  with SQLAlchemy's metadata so Alembic can detect schema changes.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# create_async_engine: single engine shared across the application lifetime.
# pool_pre_ping=True: test connections before use to handle DB restarts gracefully.
# echo=True in development prints SQL queries to stdout — disable in production.
engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

# async_sessionmaker: creates new AsyncSession objects.
# expire_on_commit=False: ORM objects remain usable after a commit.
# Without this, accessing an attribute after commit would trigger a lazy-load
# which fails in async context.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    Every model that inherits from Base is registered with SQLAlchemy's
    metadata. When Alembic runs `alembic revision --autogenerate`, it
    compares this metadata against the current DB schema to detect changes.
    """
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    Usage in a route:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            ...

    The `async with` / `yield` pattern ensures the session is always
    closed after the request, even if an exception is raised. This is
    called a "context manager dependency" in FastAPI.

    Why yield and not return? FastAPI runs any code after `yield` as cleanup
    — equivalent to a finally block. The DB session is closed here, not in
    the route handler.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
