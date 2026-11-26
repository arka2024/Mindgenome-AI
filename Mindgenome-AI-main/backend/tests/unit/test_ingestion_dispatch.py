from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest
from app.core.config import settings
from app.workers.tasks import ingestion


@pytest.mark.asyncio
async def test_ingestion_uses_api_process_by_default(monkeypatch):
    finished = asyncio.Event()

    async def process_job(job_id: str) -> None:
        assert job_id == "job-1"
        finished.set()

    celery_delay = Mock()
    monkeypatch.setattr(settings, "CELERY_ENABLED", False)
    monkeypatch.setattr(ingestion, "_async_process_document", process_job)
    monkeypatch.setattr(ingestion.process_document_ingestion, "delay", celery_delay)

    await ingestion.dispatch_document_ingestion("job-1")
    await asyncio.wait_for(finished.wait(), timeout=1)

    celery_delay.assert_not_called()


@pytest.mark.asyncio
async def test_ingestion_uses_celery_when_explicitly_enabled(monkeypatch):
    celery_delay = Mock(return_value=object())
    monkeypatch.setattr(settings, "CELERY_ENABLED", True)
    monkeypatch.setattr(ingestion.process_document_ingestion, "delay", celery_delay)

    await ingestion.dispatch_document_ingestion("job-2")

    celery_delay.assert_called_once_with("job-2")


@pytest.mark.asyncio
async def test_ingestion_falls_back_when_celery_dispatch_fails(monkeypatch):
    finished = asyncio.Event()

    async def process_job(job_id: str) -> None:
        assert job_id == "job-3"
        finished.set()

    celery_delay = Mock(side_effect=ConnectionError("broker unavailable"))
    monkeypatch.setattr(settings, "CELERY_ENABLED", True)
    monkeypatch.setattr(ingestion, "_async_process_document", process_job)
    monkeypatch.setattr(ingestion.process_document_ingestion, "delay", celery_delay)

    await ingestion.dispatch_document_ingestion("job-3")
    await asyncio.wait_for(finished.wait(), timeout=1)

    celery_delay.assert_called_once_with("job-3")
