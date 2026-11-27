from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger
from app.db.diagnostics import log_database_diagnostics


def validate_database_configuration() -> str:
    log_database_diagnostics()
    database_url = settings.async_database_url
    if settings.is_production and not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "Production must configure DATABASE_URL with a persistent PostgreSQL database. "
            "SQLite is allowed only for local development and tests."
        )
    return database_url


DATABASE_URL = validate_database_configuration()
REQUIRED_CHUNK_EMBEDDING_COLUMNS = {
    "embedding_model",
    "embedding_version",
    "embedding_dimension",
}
_production_schema_verified = False

engine_kwargs: dict[str, Any] = {
    "echo": settings.APP_DEBUG,
    "future": True,
}

if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": True,
    })

engine: AsyncEngine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session wrapped in a transaction."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def set_tenant_context(session: AsyncSession, user_id: str | None) -> None:
    """Set the PostgreSQL GUC app.current_user_id for Row Level Security."""
    if user_id and not DATABASE_URL.startswith("sqlite"):
        await session.execute(
            text("SET LOCAL app.current_user_id = :uid"),
            {"uid": str(user_id)},
        )


def _read_schema_state(connection: Connection) -> tuple[str, set[str], set[str]]:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    revisions: set[str] = set()
    if "alembic_version" in tables:
        revisions = set(
            connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
        )
    chunk_columns = (
        {column["name"] for column in inspector.get_columns("chunks")}
        if "chunks" in tables
        else set()
    )
    return connection.dialect.name, revisions, chunk_columns


def validate_production_schema_state(
    dialect: str,
    current_revisions: set[str],
    chunk_columns: set[str],
    expected_revisions: set[str],
) -> None:
    if dialect != "postgresql":
        raise RuntimeError(
            "Production database must be PostgreSQL; refusing to start against a non-production database."
        )
    if current_revisions != expected_revisions:
        raise RuntimeError(
            "Production database Alembic revision does not match this application's migration head. "
            "Run `alembic -c alembic.ini upgrade head` from the backend directory before deployment."
        )

    missing_columns = REQUIRED_CHUNK_EMBEDDING_COLUMNS - chunk_columns
    if missing_columns:
        raise RuntimeError(
            "Production chunks table is missing required embedding columns: "
            f"{', '.join(sorted(missing_columns))}. Apply the Alembic upgrade before enabling ingestion."
        )


def _expected_migration_heads() -> set[str]:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(backend_root / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(backend_root / "alembic"),
    )
    return set(ScriptDirectory.from_config(alembic_config).get_heads())


async def verify_production_schema() -> None:
    """Fail startup if the production database is not migrated to this code's head."""
    async with engine.connect() as connection:
        dialect, current_revisions, chunk_columns = await connection.run_sync(
            _read_schema_state
        )

    expected_revisions = _expected_migration_heads()
    validate_production_schema_state(
        dialect,
        current_revisions,
        chunk_columns,
        expected_revisions,
    )

    logger.info(
        "production_database_schema_verified",
        alembic_revisions=sorted(current_revisions),
        embedding_columns=sorted(REQUIRED_CHUNK_EMBEDDING_COLUMNS),
    )


async def ensure_production_schema() -> None:
    """Verify once in each process before API startup or background ingestion."""
    global _production_schema_verified
    if settings.is_production and not _production_schema_verified:
        await verify_production_schema()
        _production_schema_verified = True


async def check_db_health() -> bool:
    """Check connectivity to PostgreSQL."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.error("database_health_check_failed", error=str(exc))
        return False
