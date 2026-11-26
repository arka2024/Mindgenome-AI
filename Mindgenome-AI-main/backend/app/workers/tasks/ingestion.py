from __future__ import annotations

import asyncio
import time
import uuid
from sqlalchemy import delete, select
from app.adapters.gemini import gemini_adapter
from app.adapters.neo4j import neo4j_adapter
from app.adapters.qdrant import qdrant_adapter
from app.adapters.storage import storage_adapter
from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.document import Chapter, Chunk, Document
from app.models.enums import DocumentStatus, IngestionStatus, LLMPurpose
from app.models.learning import Concept
from app.models.meta import LLMCallLog
from app.repositories.document_repo import DocumentRepository
from app.services.document_parser import document_parser
from app.services.embedding_service import embedding_service
from app.workers.celery_app import celery_app

_background_ingestion_tasks: set[asyncio.Task[None]] = set()


async def dispatch_document_ingestion(job_id_str: str) -> None:
    if settings.CELERY_ENABLED:
        try:
            await asyncio.to_thread(process_document_ingestion.delay, job_id_str)
        except Exception as exc:
            logger.warning(
                "celery_ingestion_dispatch_failed_using_api_process",
                job_id=job_id_str,
                error=str(exc),
            )
        else:
            logger.info("document_ingestion_dispatched_to_celery", job_id=job_id_str)
            return

    task = asyncio.create_task(_async_process_document(job_id_str))
    _background_ingestion_tasks.add(task)

    def finish_ingestion(completed_task: asyncio.Task[None]) -> None:
        _background_ingestion_tasks.discard(completed_task)
        if completed_task.cancelled():
            logger.warning("document_ingestion_background_task_cancelled", job_id=job_id_str)
            return
        error = completed_task.exception()
        if error is not None:
            logger.error(
                "document_ingestion_background_task_failed",
                job_id=job_id_str,
                error=str(error),
            )

    task.add_done_callback(finish_ingestion)
    logger.info("document_ingestion_dispatched_to_api_process", job_id=job_id_str)


async def _async_process_document(job_id_str: str) -> None:
    ingestion_started_at = time.perf_counter()
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
            # Stage 1: PARSING (15%)
            await repo.update_job_status(job, IngestionStatus.PARSING, progress_pct=15, stage_detail="parsing")
            doc.status = DocumentStatus.PROCESSING
            session.add(doc)
            await session.commit()

            stage_started_at = time.perf_counter()
            file_bytes = await asyncio.to_thread(storage_adapter.download_file, doc.storage_key)

            lower_filename = doc.filename.lower()
            if lower_filename.endswith(".pdf"):
                parse_result = await asyncio.to_thread(document_parser.parse_pdf, file_bytes)
                if parse_result.is_low_text:
                    ocr_text = await gemini_adapter.ocr_pdf_bytes(file_bytes)
                    if ocr_text:
                        parse_result = await asyncio.to_thread(
                            document_parser.parse_text,
                            ocr_text.encode("utf-8"),
                        )
                        logger.info("gemini_pdf_ocr_completed", doc_id=str(doc.id), chars=len(ocr_text))
            elif lower_filename.endswith(".docx"):
                parse_result = await asyncio.to_thread(document_parser.parse_docx, file_bytes)
            elif lower_filename.endswith((".jpg", ".jpeg", ".png")):
                ocr_text = await gemini_adapter.ocr_image_bytes(file_bytes)
                if not ocr_text:
                    raise ValueError("Gemini OCR returned no readable text")
                parse_result = await asyncio.to_thread(
                    document_parser.parse_text,
                    ocr_text.encode("utf-8"),
                )
                logger.info("gemini_image_ocr_completed", doc_id=str(doc.id), chars=len(ocr_text))
            else:
                parse_result = await asyncio.to_thread(document_parser.parse_text, file_bytes)

            logger.info(
                "document_ingestion_stage_completed",
                doc_id=str(doc.id),
                stage="parsing",
                duration_ms=round((time.perf_counter() - stage_started_at) * 1000),
                bytes=len(file_bytes),
                pages=parse_result.page_count,
                chunks=len(parse_result.chunks),
            )

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

            # Stage 2: CHUNKING (35%)
            stage_started_at = time.perf_counter()
            await repo.update_job_status(job, IngestionStatus.CHUNKING, progress_pct=35, stage_detail="chunking")
            await session.commit()

            # A reprocess must replace prior document-scoped rows before ordinal values restart.
            await qdrant_adapter.delete_by_document(str(doc.user_id), str(doc.id))
            await session.execute(delete(Chunk).where(Chunk.document_id == doc.id))
            await session.execute(delete(Chapter).where(Chapter.document_id == doc.id))

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
                    qdrant_point_id=uuid.uuid4(),
                )
                for ck in parse_result.chunks
            ]
            await repo.create_chunks(db_chunks)
            await session.commit()
            logger.info(
                "document_ingestion_stage_completed",
                doc_id=str(doc.id),
                stage="chunking",
                duration_ms=round((time.perf_counter() - stage_started_at) * 1000),
                chunks=len(db_chunks),
            )

            # Stage 3: EMBEDDING (55%)
            await repo.update_job_status(job, IngestionStatus.EMBEDDING, progress_pct=55, stage_detail="embedding")
            await session.commit()
            chunk_texts = [ck.body for ck in db_chunks]
            stage_started_at = time.perf_counter()
            chunk_embeddings = await asyncio.to_thread(embedding_service.embed_batch, chunk_texts)
            logger.info(
                "document_ingestion_stage_completed",
                doc_id=str(doc.id),
                stage="embedding",
                duration_ms=round((time.perf_counter() - stage_started_at) * 1000),
                chunks=len(chunk_embeddings),
            )

            # Upsert into Qdrant
            qdrant_points = [
                {
                    "id": str(ck.id),
                    "vector": emb,
                    "payload": {
                        "user_id": str(doc.user_id),
                        "document_id": str(doc.id),
                        "chunk_id": str(ck.id),
                        "chapter_id": str(ck.chapter_id) if ck.chapter_id else None,
                        "page_start": ck.page_start,
                        "page_end": ck.page_end,
                        "token_count": ck.token_count,
                    },
                }
                for ck, emb in zip(db_chunks, chunk_embeddings)
            ]
            stage_started_at = time.perf_counter()
            await qdrant_adapter.upsert_points(qdrant_points)
            await session.commit()
            logger.info(
                "document_ingestion_stage_completed",
                doc_id=str(doc.id),
                stage="vector_storage",
                duration_ms=round((time.perf_counter() - stage_started_at) * 1000),
                points=len(qdrant_points),
            )

            # Stage 4: EXTRACTING Concepts & Prerequisites via Gemini (75%)
            await repo.update_job_status(job, IngestionStatus.EXTRACTING, progress_pct=75, stage_detail="extracting")
            await session.commit()
            combined_summary_text = "\n\n".join(chunk_texts[:4])
            system_prompt = (
                "You are the MindGenome AI Concept Extraction engine. Extract key academic concepts, "
                "normalized lemmas, short definitions, and prerequisite relationships from the text DATA. "
                "Output JSON matching ConceptExtractionPayload."
            )
            user_prompt = f"Document: {doc.filename}\n\nDATA:\n{combined_summary_text}"

            stage_started_at = time.perf_counter()
            extraction_json, audit = await gemini_adapter.generate_structured_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                purpose=LLMPurpose.CONCEPT_EXTRACT,
                user_id=str(doc.user_id),
            )
            logger.info(
                "document_ingestion_stage_completed",
                doc_id=str(doc.id),
                stage="concept_extraction",
                duration_ms=round((time.perf_counter() - stage_started_at) * 1000),
                concepts=len(extraction_json.get("concepts", [])),
            )

            # Audit LLM call
            call_log = LLMCallLog(
                user_id=doc.user_id,
                prompt_version=audit["prompt_version"],
                model=audit["model"],
                purpose=audit["purpose"],
                input_tokens=audit.get("input_tokens"),
                output_tokens=audit.get("output_tokens"),
                cost_usd=audit.get("cost_usd"),
                latency_ms=audit.get("latency_ms"),
                status=audit["status"],
                error_message=audit.get("error_message"),
            )
            session.add(call_log)

            # Stage 5: GRAPH_BUILT - Neo4j & PostgreSQL Concept sync (90%)
            stage_started_at = time.perf_counter()
            await repo.update_job_status(job, IngestionStatus.GRAPH_BUILT, progress_pct=90, stage_detail="graph_built")
            await session.commit()
            raw_concepts = extraction_json.get("concepts", [])
            concept_name_to_id: dict[str, uuid.UUID] = {}
            concepts_by_name: dict[str, dict[str, str]] = {}
            for c in raw_concepts:
                c_name = c.get("canonical_name", "").strip()
                norm_name = c.get("normalized_name", c_name.lower()).strip().lower()
                lemma = c.get("lemma", norm_name).strip()
                definition = c.get("definition", "").strip()

                if not c_name:
                    continue
                concepts_by_name.setdefault(
                    norm_name,
                    {
                        "canonical_name": c_name,
                        "lemma": lemma,
                        "definition": definition,
                    },
                )

            normalized_names = list(concepts_by_name)
            existing_result = await session.execute(
                select(Concept).where(
                    Concept.user_id == doc.user_id,
                    Concept.normalized_name.in_(normalized_names),
                )
            )
            concepts_by_id = {concept.normalized_name: concept for concept in existing_result.scalars()}
            for norm_name, concept_data in concepts_by_name.items():
                if norm_name not in concepts_by_id:
                    concept = Concept(
                        user_id=doc.user_id,
                        canonical_name=concept_data["canonical_name"],
                        normalized_name=norm_name,
                        lemma=concept_data["lemma"],
                        definition=concept_data["definition"],
                    )
                    session.add(concept)
                    concepts_by_id[norm_name] = concept
            await session.flush()

            neo4j_concepts = []
            for norm_name, concept in concepts_by_id.items():
                concept_name_to_id[norm_name] = concept.id
                neo4j_concepts.append(
                    {
                        "concept_id": str(concept.id),
                        "name": concepts_by_name[norm_name]["canonical_name"],
                        "normalized_name": norm_name,
                    }
                )
            await neo4j_adapter.merge_concepts(str(doc.user_id), neo4j_concepts)

            # Write Prerequisite Edges with Cycle Guard
            for c in raw_concepts:
                target_norm = c.get("normalized_name", "").strip().lower()
                target_id = concept_name_to_id.get(target_norm)
                if not target_id:
                    continue
                prereqs = c.get("prerequisites", [])
                for p_name in prereqs:
                    p_norm = p_name.strip().lower()
                    p_id = concept_name_to_id.get(p_norm)
                    if p_id and p_id != target_id:
                        # Merge prerequisite edge A -> B with cycle check
                        await neo4j_adapter.merge_prerequisite_edge(
                            user_id=str(doc.user_id),
                            from_concept_id=str(p_id),
                            to_concept_id=str(target_id),
                            confidence=0.85,
                            status="confirmed",
                        )

            await session.commit()
            logger.info(
                "document_ingestion_stage_completed",
                doc_id=str(doc.id),
                stage="graph_build",
                duration_ms=round((time.perf_counter() - stage_started_at) * 1000),
                concepts=len(raw_concepts),
            )

            # Stage 6: READY (100%)
            await repo.update_job_status(job, IngestionStatus.READY, progress_pct=100, stage_detail="ready")
            doc.status = DocumentStatus.READY
            session.add(doc)
            await session.commit()

            logger.info(
                "document_ingestion_complete",
                doc_id=str(doc.id),
                chunks=len(db_chunks),
                concepts=len(raw_concepts),
                duration_ms=round((time.perf_counter() - ingestion_started_at) * 1000),
            )

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
