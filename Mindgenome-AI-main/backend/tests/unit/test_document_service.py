from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app.models.enums import IngestionStatus
from app.services import document_service as service_module
from app.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_upload_commits_job_before_dispatch(monkeypatch):
    user_id = uuid.uuid4()
    document_id = uuid.uuid4()
    job_id = uuid.uuid4()
    session = SimpleNamespace(commit=AsyncMock())
    service = DocumentService(session)
    service.repo = SimpleNamespace(
        get_by_sha256=AsyncMock(return_value=None),
        create_document=AsyncMock(return_value=SimpleNamespace(id=document_id)),
        create_ingestion_job=AsyncMock(
            return_value=SimpleNamespace(id=job_id, status=IngestionStatus.QUEUED)
        ),
    )
    storage_upload = Mock()
    monkeypatch.setattr(service_module.storage_adapter, "upload_file", storage_upload)
    monkeypatch.setattr(
        service_module,
        "validate_and_inspect_upload",
        Mock(return_value=("notes.txt", "text/plain", 5, "a" * 64)),
    )

    async def dispatch(job_id_str: str) -> None:
        assert job_id_str == str(job_id)
        session.commit.assert_awaited_once()

    monkeypatch.setattr(service_module, "dispatch_document_ingestion", dispatch)

    result = await service.upload_document(
        user=SimpleNamespace(id=user_id),
        filename="notes.txt",
        content=b"notes",
        idempotency_key="upload-test",
    )

    assert result.document_id == document_id
    assert result.job_id == job_id
    session.commit.assert_awaited_once()
    storage_upload.assert_called_once()
