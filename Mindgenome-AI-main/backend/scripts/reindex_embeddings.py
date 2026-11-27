from __future__ import annotations

import argparse
import asyncio
import uuid

from sqlalchemy import or_, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.document import Chunk, Document, IngestionJob
from app.models.enums import IngestionStatus
from app.repositories.document_repo import DocumentRepository
from app.workers.tasks.ingestion import _async_process_document, dispatch_document_ingestion


async def documents_needing_reindex(limit: int | None = None) -> list[tuple[uuid.UUID, uuid.UUID]]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Document.id, Document.user_id)
            .join(Chunk, Chunk.document_id == Document.id)
            .where(
                Document.deleted_at.is_(None),
                or_(
                    Chunk.embedding_model.is_(None),
                    Chunk.embedding_model != settings.EMBEDDING_MODEL,
                    Chunk.embedding_version.is_(None),
                    Chunk.embedding_version != settings.EMBEDDING_VERSION,
                    Chunk.embedding_dimension.is_(None),
                    Chunk.embedding_dimension != settings.EMBEDDING_DIMENSION,
                ),
            )
            .distinct()
            .order_by(Document.id)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return [(row.id, row.user_id) for row in (await session.execute(stmt)).all()]


async def reindex_embeddings(limit: int | None = None, dry_run: bool = False) -> int:
    documents = await documents_needing_reindex(limit)
    print(
        f"Found {len(documents)} documents needing embedding version "
        f"{settings.EMBEDDING_VERSION} ({settings.EMBEDDING_DIMENSION} dimensions)."
    )
    if dry_run:
        return 0

    enqueued = 0
    for document_id, user_id in documents:
        async with AsyncSessionLocal() as session:
            active_job = await session.execute(
                select(Document.id)
                .join(IngestionJob, IngestionJob.document_id == Document.id)
                .where(
                    Document.id == document_id,
                    IngestionJob.status.in_(
                        [
                            IngestionStatus.QUEUED,
                            IngestionStatus.PARSING,
                            IngestionStatus.CHUNKING,
                            IngestionStatus.EMBEDDING,
                            IngestionStatus.EXTRACTING,
                            IngestionStatus.GRAPH_BUILT,
                        ]
                    ),
                )
                .limit(1)
            )
            if active_job.scalar_one_or_none() is not None:
                print(f"Skipping {document_id}: an ingestion job is already active.")
                continue

            repo = DocumentRepository(session)
            job = await repo.create_ingestion_job(
                user_id=user_id,
                document_id=document_id,
                idempotency_key=f"embedding-reindex-{settings.EMBEDDING_VERSION}-{uuid.uuid4()}",
            )
            job_id = str(job.id)
            await session.commit()

        if settings.CELERY_ENABLED:
            await dispatch_document_ingestion(job_id)
        else:
            await _async_process_document(job_id)
        enqueued += 1
        print(f"Submitted reindex job for document {document_id}.")

    return enqueued


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-embed existing documents using the configured embedding model."
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of documents.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report how many documents need reindexing.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    asyncio.run(reindex_embeddings(limit=args.limit, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
