from __future__ import annotations

import pytest

from app.core.config import settings
from app.db import diagnostics
from app.db.session import (
    validate_database_configuration,
    validate_production_schema_state,
)


def test_render_environment_is_treated_as_production(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "local")
    monkeypatch.setattr(settings, "RENDER", True)
    monkeypatch.setattr(settings, "RENDER_SERVICE_ID", "")

    assert settings.is_production
    assert settings.runtime_environment == "production"


def test_render_service_id_is_treated_as_production(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "local")
    monkeypatch.setattr(settings, "RENDER", False)
    monkeypatch.setattr(settings, "RENDER_SERVICE_ID", "srv-example")

    assert settings.is_production


def test_production_rejects_sqlite_database(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "RENDER", False)
    monkeypatch.setattr(settings, "RENDER_SERVICE_ID", "")
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite+aiosqlite:///./local.db")

    with pytest.raises(RuntimeError, match="persistent PostgreSQL"):
        validate_database_configuration()


def test_invalid_database_url_diagnostic_does_not_prevent_production_validation(
    monkeypatch,
):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "RENDER", False)
    monkeypatch.setattr(settings, "RENDER_SERVICE_ID", "")
    monkeypatch.setattr(settings, "DATABASE_URL", "://invalid-url")

    logged_records = []

    class DiagnosticLogger:
        def info(self, event, **fields):
            logged_records.append((event, fields))

    monkeypatch.setattr(diagnostics, "logger", DiagnosticLogger())
    monkeypatch.setattr(diagnostics, "setup_logging", lambda: None)
    monkeypatch.setattr(
        type(settings),
        "async_database_url",
        property(lambda self: "sqlite+aiosqlite:///./local.db"),
    )

    with pytest.raises(RuntimeError, match="persistent PostgreSQL"):
        validate_database_configuration()

    assert logged_records == [
        (
            "temporary_database_diagnostic",
            {
                "database_driver": "unknown",
                "database_url_configured": True,
            },
        )
    ]
    assert "://invalid-url" not in repr(logged_records)


def test_sqlite_diagnostic_reads_existing_file_without_modifying_it(tmp_path):
    import sqlite3

    database_path = tmp_path / "existing.db"
    connection = sqlite3.connect(database_path)
    connection.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
    connection.execute("INSERT INTO documents DEFAULT VALUES")
    connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32))")
    connection.execute(
        "INSERT INTO alembic_version (version_num) VALUES ('002_embedding_provenance')"
    )
    connection.commit()
    connection.close()
    original_bytes = database_path.read_bytes()

    result = diagnostics.inspect_sqlite_database(database_path)

    assert result["sqlite_file_exists"] is True
    assert result["sqlite_tables"] == ["alembic_version", "documents"]
    assert result["sqlite_record_counts"] == {"alembic_version": 1, "documents": 1}
    assert result["alembic_revision_table_exists"] is True
    assert result["alembic_current_revision"] == ["002_embedding_provenance"]
    assert result["sqlite_inspection_status"] == "complete"
    assert database_path.read_bytes() == original_bytes


def test_sqlite_diagnostic_does_not_create_missing_file(tmp_path):
    database_path = tmp_path / "missing.db"

    result = diagnostics.inspect_sqlite_database(database_path)

    assert result["sqlite_file_exists"] is False
    assert result["sqlite_inspection_status"] == "not_accessible"
    assert not database_path.exists()


def test_production_database_url_is_normalized_for_asyncpg(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "RENDER", False)
    monkeypatch.setattr(settings, "RENDER_SERVICE_ID", "")
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        "postgresql://test_user:test_password@db.example.test/mindgenome?sslmode=require",
    )

    assert settings.async_database_url == (
        "postgresql+asyncpg://test_user:test_password@db.example.test/mindgenome?ssl=require"
    )
    assert validate_database_configuration() == settings.async_database_url


def test_production_schema_requires_database_migration_head():
    with pytest.raises(RuntimeError, match="Alembic revision"):
        validate_production_schema_state(
            "postgresql",
            {"001_initial"},
            {"embedding_model", "embedding_version", "embedding_dimension"},
            {"002_embedding_provenance"},
        )


def test_production_schema_requires_embedding_columns():
    with pytest.raises(RuntimeError, match="embedding_dimension"):
        validate_production_schema_state(
            "postgresql",
            {"002_embedding_provenance"},
            {"embedding_model", "embedding_version"},
            {"002_embedding_provenance"},
        )


def test_production_schema_rejects_non_postgresql_database():
    with pytest.raises(RuntimeError, match="must be PostgreSQL"):
        validate_production_schema_state(
            "sqlite",
            {"002_embedding_provenance"},
            {"embedding_model", "embedding_version", "embedding_dimension"},
            {"002_embedding_provenance"},
        )
