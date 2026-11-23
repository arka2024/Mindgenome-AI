from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.document import Chapter, Chunk, Document, IngestionJob
from app.models.enums import DocumentStatus, IngestionStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_document(
        self,
        user_id: uuid.UUID,
        filename: str,
        content_type: str,
        byte_size: int,
        storage_key: str,
        sha256: str,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            byte_size=byte_size,
            storage_key=storage_key,
            sha256=sha256,
            status=DocumentStatus.UPLOADED,
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get_by_id(self, document_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id, Document.deleted_at.is_(None))
            .options(
                selectinload(Document.chapters),
                selectinload(Document.jobs),
            )
        )
        if user_id:
            stmt = stmt.where(Document.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sha256(self, user_id: uuid.UUID, sha256: str) -> Document | None:
        stmt = select(Document).where(
            Document.user_id == user_id,
            Document.sha256 == sha256,
            Document.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_documents(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Document], int]:
        count_stmt = select(func.count(Document.id)).where(
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        )
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Document)
            .where(Document.user_id == user_id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(selectinload(Document.chapters))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def delete_document(self, document: Document) -> None:
        now = datetime.now(timezone.utc)
        document.deleted_at = now
        self.session.add(document)
        await self.session.flush()

    async def create_chapters(self, chapters: list[Chapter]) -> None:
        self.session.add_all(chapters)
        await self.session.flush()

    async def create_chunks(self, chunks: list[Chunk]) -> None:
        self.session.add_all(chunks)
        await self.session.flush()

    # -------------------------------------------------------------------------
    # Ingestion Jobs
    # -------------------------------------------------------------------------

    async def create_ingestion_job(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        idempotency_key: str,
    ) -> IngestionJob:
        job = IngestionJob(
            user_id=user_id,
            document_id=document_id,
            status=IngestionStatus.QUEUED,
            progress_pct=5,
            stage_detail="queued",
            idempotency_key=idempotency_key,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_by_id(self, job_id: uuid.UUID, user_id: uuid.UUID | None = None) -> IngestionJob | None:
        stmt = select(IngestionJob).where(IngestionJob.id == job_id)
        if user_id:
            stmt = stmt.where(IngestionJob.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_job_for_document(self, document_id: uuid.UUID, user_id: uuid.UUID | None = None) -> IngestionJob | None:
        stmt = (
            select(IngestionJob)
            .where(IngestionJob.document_id == document_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(1)
        )
        if user_id:
            stmt = stmt.where(IngestionJob.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job: IngestionJob,
        status: IngestionStatus,
        progress_pct: int,
        stage_detail: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        job.status = status
        job.progress_pct = progress_pct
        job.stage_detail = stage_detail or status.value
        job.updated_at = datetime.now(timezone.utc)
        if error_code:
            job.error_code = error_code
        if error_message:
            job.error_message = error_message
        if status == IngestionStatus.PARSING and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        if status in (IngestionStatus.READY, IngestionStatus.FAILED):
            job.finished_at = datetime.now(timezone.utc)

        self.session.add(job)
        await self.session.flush()
