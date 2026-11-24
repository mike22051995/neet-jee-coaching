"""
Alembic environment configuration.

Alembic uses this file to know:
1. How to connect to the database (sync engine for migrations).
2. Which SQLAlchemy metadata to compare against (from our models).

We use a *sync* connection for Alembic (not async), because Alembic's migration
engine runs outside of the async event loop. We use psycopg2 (sync) rather than
asyncpg here, configured via a re-written URL.

Layer: DB / Migration tooling
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import the Base so Alembic can see all model metadata
from app.db.base import Base
import app.models  # noqa: F401 — registers all models with Base.metadata
from app.core.config import get_settings

settings = get_settings()

# Alembic Config object (from alembic.ini)
config = context.config

# Override sqlalchemy.url with the value from our app config
config.set_main_option("sqlalchemy.url", settings.async_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the SQLAlchemy MetaData that Alembic compares against the DB schema
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
