from __future__ import annotations

import uuid
from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    IngestionJobResponse,
    UploadAcceptedResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(tags=["documents"])


@router.post(
    "/documents",
    response_model=UploadAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@router.post(
    "/documents/upload",
    response_model=UploadAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UploadAcceptedResponse:
    content = await file.read()
    key = idempotency_key or f"upload-{uuid.uuid4()}"
    service = DocumentService(session)
    return await service.upload_document(
        user=user,
        filename=file.filename or "upload.pdf",
        content=content,
        idempotency_key=key,
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    service = DocumentService(session)
    return await service.list_documents(user=user, page=page, page_size=page_size)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    service = DocumentService(session)
    return await service.get_document(user=user, document_id=document_id)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = DocumentService(session)
    await service.delete_document(user=user, document_id=document_id)
    return None


@router.get("/documents/{document_id}/status", response_model=IngestionJobResponse)
async def get_document_status(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    service = DocumentService(session)
    doc = await service.get_document(user=user, document_id=document_id)
    if not doc.job_id:
        raise NotFoundException(detail="No ingestion job recorded for this document.")
    return await service.get_job_status(user=user, job_id=doc.job_id)


@router.post("/documents/{document_id}/reprocess", response_model=UploadAcceptedResponse)
async def reprocess_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UploadAcceptedResponse:
    service = DocumentService(session)
    return await service.reprocess_document(user=user, document_id=document_id)


@router.get("/ingestion-jobs/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    service = DocumentService(session)
    return await service.get_job_status(user=user, job_id=job_id)
