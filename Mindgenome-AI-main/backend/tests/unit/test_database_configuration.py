from __future__ import annotations

import pytest

from app.core.config import settings
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
