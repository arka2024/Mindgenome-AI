from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.logging import logger, setup_logging


def _sqlite_database_path(database: str | None) -> Path | None:
    if not database or database == ":memory:":
        return None

    path = Path(database)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def inspect_sqlite_database(path: Path) -> dict[str, Any]:
    """Inspect an existing SQLite file without creating or changing it."""
    result: dict[str, Any] = {
        "sqlite_file_exists": path.is_file(),
        "sqlite_tables": [],
        "sqlite_record_counts": {},
        "alembic_revision_table_exists": False,
        "alembic_current_revision": None,
        "sqlite_inspection_status": "not_accessible",
    }
    if not result["sqlite_file_exists"]:
        return result

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            f"{path.as_uri()}?mode=ro",
            uri=True,
            timeout=2,
        )
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        result["sqlite_tables"] = tables
        counts = {}
        for table in tables:
            quoted_table = '"' + table.replace('"', '""') + '"'
            counts[table] = connection.execute(
                f"SELECT COUNT(*) FROM {quoted_table}"
            ).fetchone()[0]
        result["sqlite_record_counts"] = counts

        if "alembic_version" in tables:
            result["alembic_revision_table_exists"] = True
            result["alembic_current_revision"] = [
                row[0]
                for row in connection.execute(
                    "SELECT version_num FROM alembic_version"
                )
            ]
        result["sqlite_inspection_status"] = "complete"
    except sqlite3.Error as exc:
        # Exception messages can contain SQL or filesystem details; log only the type.
        result["sqlite_inspection_status"] = "error"
        result["sqlite_inspection_error_type"] = type(exc).__name__
    finally:
        if connection is not None:
            connection.close()

    return result


def log_database_diagnostics() -> None:
    """Temporary startup-only, read-only diagnostics; remove after production audit."""
    if not settings.is_production:
        return

    setup_logging()

    configured = (
        "DATABASE_URL" in settings.model_fields_set
        and bool(settings.DATABASE_URL.strip())
    )
    try:
        parsed_url = make_url(settings.DATABASE_URL)
        raw_driver = parsed_url.drivername.lower()
        if raw_driver.startswith("sqlite"):
            database_driver = "SQLite"
        elif raw_driver.startswith(("postgres", "postgresql")):
            database_driver = "PostgreSQL"
        else:
            database_driver = "other"
    except (ArgumentError, TypeError, ValueError):
        parsed_url = None
        database_driver = "unknown"

    details: dict[str, Any] = {
        "database_driver": database_driver,
        "database_url_configured": configured,
    }

    if database_driver == "SQLite" and parsed_url is not None:
        database_path = _sqlite_database_path(parsed_url.database)
        if database_path is None:
            details.update(
                sqlite_database_path=parsed_url.database or ":memory:",
                storage_persistence="non_persistent_in_memory",
                sqlite_file_exists=False,
                sqlite_tables=[],
                sqlite_record_counts={},
                alembic_revision_table_exists=False,
                alembic_current_revision=None,
                sqlite_inspection_status="in_memory_database_not_inspected",
            )
        else:
            details["sqlite_database_path"] = str(database_path)
            details["storage_persistence"] = (
                "unknown_render_disk_mount_not_declared_in_backend_configuration"
                if settings.is_production
                else "host_managed_local_storage"
            )
            try:
                details.update(inspect_sqlite_database(database_path))
            except OSError as exc:
                details.update(
                    sqlite_file_exists=database_path.is_file(),
                    sqlite_tables=[],
                    sqlite_record_counts={},
                    alembic_revision_table_exists=False,
                    alembic_current_revision=None,
                    sqlite_inspection_status="error",
                    sqlite_inspection_error_type=type(exc).__name__,
                )

    logger.info("temporary_database_diagnostic", **details)
