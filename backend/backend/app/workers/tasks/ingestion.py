from __future__ import annotations

import asyncio
import uuid
from app.adapters.storage import storage_adapter
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.document import Chapter, Chunk
from app.models.enums import DocumentStatus, IngestionStatus
from app.repositories.document_repo import DocumentRepository
from app.services.document_parser import document_parser
from app.workers.celery_app import celery_app


async def _async_process_document(job_id_str: str) -> None:
    job_id = uuid.UUID(job_id_str)
    async with AsyncSessionLocal() as session:
        repo = DocumentRepository(session)
        job = await repo.get_job_by_id(job_id)
        if not job:
            logger.error("ingestion_job_not_found", job_id=job_id_str)
            return

        doc = await repo.get_by_id(job.document_id)
        if not doc:
            logger.error("document_not_found_for_job", job_id=job_id_str, doc_id=str(job.document_id))
            await repo.update_job_status(
                job,
                status=IngestionStatus.FAILED,
                progress_pct=100,
                error_code="document_missing",
                error_message="Document record could not be found.",
            )
            await session.commit()
            return

        try:
            # Stage 1: PARSING
            await repo.update_job_status(job, IngestionStatus.PARSING, progress_pct=15, stage_detail="parsing")
            doc.status = DocumentStatus.PROCESSING
            session.add(doc)
            await session.commit()

            # Download document bytes
            file_bytes = storage_adapter.download_file(doc.storage_key)

            # Parse content
            if doc.filename.lower().endswith(".pdf"):
                parse_result = document_parser.parse_pdf(file_bytes)
            else:
                parse_result = document_parser.parse_docx(file_bytes)

            doc.page_count = parse_result.page_count
            doc.is_low_text = parse_result.is_low_text
            doc.low_text_warning = parse_result.low_text_warning

            if parse_result.is_low_text and not parse_result.chunks:
                await repo.update_job_status(
                    job,
                    status=IngestionStatus.FAILED,
                    progress_pct=100,
                    error_code="low_text",
                    error_message=parse_result.low_text_warning or "Document text extraction yielded insufficient text.",
                )
                doc.status = DocumentStatus.FAILED
                session.add(doc)
                await session.commit()
                return

            # Stage 2: CHUNKING
            await repo.update_job_status(job, IngestionStatus.CHUNKING, progress_pct=35, stage_detail="chunking")

            # Persist chapters
            db_chapters = [
                Chapter(
                    user_id=doc.user_id,
                    document_id=doc.id,
                    title=ch.title,
                    ordinal=ch.ordinal,
                    start_page=ch.start_page,
                    end_page=ch.end_page,
                )
                for ch in parse_result.chapters
            ]
            await repo.create_chapters(db_chapters)

            # Persist chunks
            db_chunks = [
                Chunk(
                    user_id=doc.user_id,
                    document_id=doc.id,
                    chapter_id=db_chapters[0].id if db_chapters else None,
                    ordinal=ck.ordinal,
                    page_start=ck.page_start,
                    page_end=ck.page_end,
                    heading_path=ck.heading_path,
                    body=ck.body,
                    token_count=ck.token_count,
                )
                for ck in parse_result.chunks
            ]
            await repo.create_chunks(db_chunks)
            await session.commit()

            # Stage 3: EMBEDDING (progress 55%)
            await repo.update_job_status(job, IngestionStatus.EMBEDDING, progress_pct=55, stage_detail="embedding")
            await session.commit()

            # Stage 4: EXTRACTING (progress 75%)
            await repo.update_job_status(job, IngestionStatus.EXTRACTING, progress_pct=75, stage_detail="extracting")
            await session.commit()

            # Stage 5: GRAPH_BUILT (progress 90%)
            await repo.update_job_status(job, IngestionStatus.GRAPH_BUILT, progress_pct=90, stage_detail="graph_built")
            await session.commit()

            # Stage 6: READY (progress 100%)
            await repo.update_job_status(job, IngestionStatus.READY, progress_pct=100, stage_detail="ready")
            doc.status = DocumentStatus.READY
            session.add(doc)
            await session.commit()

            logger.info("document_ingestion_complete", doc_id=str(doc.id), chunks=len(db_chunks))

        except Exception as exc:
            logger.exception("ingestion_job_failed", job_id=job_id_str, error=str(exc))
            await session.rollback()
            await repo.update_job_status(
                job,
                status=IngestionStatus.FAILED,
                progress_pct=100,
                error_code="processing_error",
                error_message=str(exc),
            )
            doc.status = DocumentStatus.FAILED
            session.add(doc)
            await session.commit()


@celery_app.task(bind=True, max_retries=3)
def process_document_ingestion(self, job_id_str: str) -> None:
    """Celery task entry point."""
    try:
        asyncio.run(_async_process_document(job_id_str))
    except Exception as exc:
        logger.error("celery_task_exception_retrying", job_id=job_id_str, error=str(exc))
        raise self.retry(exc=exc, countdown=10)
