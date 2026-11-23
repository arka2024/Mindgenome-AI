from __future__ import annotations

import io
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.storage import storage_adapter
from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import logger
from app.adapters.redis import rate_limiter
from app.core.upload_validation import validate_and_inspect_upload
from app.models.enums import DocumentStatus, IngestionStatus
from app.models.user import User
from app.repositories.document_repo import DocumentRepository
from app.schemas.document import (
    ChapterResponse,
    DocumentListResponse,
    DocumentResponse,
    IngestionJobResponse,
    UploadAcceptedResponse,
)
from app.workers.tasks.ingestion import _async_process_document, process_document_ingestion


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DocumentRepository(session)

    async def upload_document(
        self,
        user: User,
        filename: str,
        content: bytes,
        idempotency_key: str,
        background: bool = True,
    ) -> UploadAcceptedResponse:
        # 1. Validate file content and magic bytes
        safe_name, verified_mime, byte_size, sha256 = validate_and_inspect_upload(
            filename=filename,
            content=content,
        )

        # 2. Check for duplicate upload by the same user
        existing_doc = await self.repo.get_by_sha256(user.id, sha256)
        if existing_doc:
            latest_job = await self.repo.get_latest_job_for_document(existing_doc.id, user.id)
            return UploadAcceptedResponse(
                document_id=existing_doc.id,
                job_id=latest_job.id if latest_job else existing_doc.id,
                status=existing_doc.status.value,
            )

        # 3. Create document record
        doc_id = uuid.uuid4()
        storage_key = storage_adapter.generate_storage_key(
            user_id=str(user.id),
            document_id=str(doc_id),
            filename=safe_name,
        )

        # 4. Upload to S3/MinIO
        storage_adapter.upload_file(
            file_obj=io.BytesIO(content),
            storage_key=storage_key,
            content_type=verified_mime,
        )

        doc = await self.repo.create_document(
            user_id=user.id,
            filename=safe_name,
            content_type=verified_mime,
            byte_size=byte_size,
            storage_key=storage_key,
            sha256=sha256,
        )

        # 5. Create ingestion job
        job = await self.repo.create_ingestion_job(
            user_id=user.id,
            document_id=doc.id,
            idempotency_key=idempotency_key,
        )

        # 6. Dispatch background task
        if background:
            redis_client = await rate_limiter.get_client()
            if redis_client is None:
                import asyncio
                asyncio.create_task(_async_process_document(str(job.id)))
            else:
                try:
                    process_document_ingestion.delay(str(job.id))
                except Exception:
                    import asyncio
                    asyncio.create_task(_async_process_document(str(job.id)))
        else:
            await _async_process_document(str(job.id))

        logger.info("document_uploaded_job_created", doc_id=str(doc.id), job_id=str(job.id))
        return UploadAcceptedResponse(
            document_id=doc.id,
            job_id=job.id,
            status=job.status.value,
        )

    async def list_documents(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentListResponse:
        docs, total = await self.repo.list_user_documents(user.id, page=page, page_size=page_size)
        items: list[DocumentResponse] = []
        for d in docs:
            latest_job = await self.repo.get_latest_job_for_document(d.id, user.id)
            items.append(
                DocumentResponse(
                    id=d.id,
                    filename=d.filename,
                    status=d.status.value,
                    page_count=d.page_count,
                    is_low_text=d.is_low_text,
                    low_text_warning=d.low_text_warning,
                    created_at=d.created_at,
                    job_id=latest_job.id if latest_job else None,
                    chapters=[
                        ChapterResponse(
                            id=ch.id,
                            title=ch.title,
                            page_start=ch.start_page,
                            page_end=ch.end_page,
                        )
                        for ch in d.chapters
                    ],
                )
            )
        return DocumentListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_document(self, user: User, document_id: uuid.UUID) -> DocumentResponse:
        doc = await self.repo.get_by_id(document_id, user.id)
        if not doc:
            raise NotFoundException(detail="Document not found.")

        latest_job = await self.repo.get_latest_job_for_document(doc.id, user.id)
        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status.value,
            page_count=doc.page_count,
            is_low_text=doc.is_low_text,
            low_text_warning=doc.low_text_warning,
            created_at=doc.created_at,
            job_id=latest_job.id if latest_job else None,
            chapters=[
                ChapterResponse(
                    id=ch.id,
                    title=ch.title,
                    page_start=ch.start_page,
                    page_end=ch.end_page,
                )
                for ch in doc.chapters
            ],
        )

    async def delete_document(self, user: User, document_id: uuid.UUID) -> None:
        doc = await self.repo.get_by_id(document_id, user.id)
        if not doc:
            raise NotFoundException(detail="Document not found.")

        await self.repo.delete_document(doc)
        storage_adapter.delete_file(doc.storage_key)
        logger.info("document_deleted", doc_id=str(document_id), user_id=str(user.id))

    async def get_job_status(self, user: User, job_id: uuid.UUID) -> IngestionJobResponse:
        job = await self.repo.get_job_by_id(job_id, user.id)
        if not job:
            raise NotFoundException(detail="Ingestion job not found.")

        return IngestionJobResponse(
            id=job.id,
            document_id=job.document_id,
            status=job.status.value,
            progress_pct=job.progress_pct,
            stage_detail=job.stage_detail,
            error_code=job.error_code,
            error_message=job.error_message,
        )

    async def reprocess_document(self, user: User, document_id: uuid.UUID) -> UploadAcceptedResponse:
        doc = await self.repo.get_by_id(document_id, user.id)
        if not doc:
            raise NotFoundException(detail="Document not found.")

        idempotency_key = f"reprocess-{uuid.uuid4()}"
        job = await self.repo.create_ingestion_job(
            user_id=user.id,
            document_id=doc.id,
            idempotency_key=idempotency_key,
        )

        redis_client = await rate_limiter.get_client()
        if redis_client is None:
            import asyncio
            asyncio.create_task(_async_process_document(str(job.id)))
        else:
            try:
                process_document_ingestion.delay(str(job.id))
            except Exception:
                import asyncio
                asyncio.create_task(_async_process_document(str(job.id)))

        return UploadAcceptedResponse(
            document_id=doc.id,
            job_id=job.id,
            status=job.status.value,
        )
