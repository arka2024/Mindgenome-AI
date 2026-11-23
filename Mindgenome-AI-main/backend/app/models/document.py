from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import DocumentStatus, IngestionStatus


class Document(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.UPLOADED,
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_low_text: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    low_text_warning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="documents")  # type: ignore # noqa: F821
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chapter.ordinal",
    )
    chunks: Mapped[list[Chunk]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chunk.ordinal",
    )
    jobs: Mapped[list[IngestionJob]] = relationship(
        "IngestionJob",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("byte_size > 0 AND byte_size <= 26214400", name="documents_byte_size_check"),
        UniqueConstraint("user_id", "sha256", name="documents_user_sha_unique"),
    )


class Chapter(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chapters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped[Document] = relationship("Document", back_populates="chapters")
    chunks: Mapped[list[Chunk]] = relationship("Chunk", back_populates="chapter")

    __table_args__ = (
        CheckConstraint("ordinal >= 0", name="chapters_ordinal_check"),
        CheckConstraint("start_page >= 1", name="chapters_start_page_check"),
        CheckConstraint("end_page >= start_page", name="chapters_page_range_check"),
        UniqueConstraint("document_id", "ordinal", name="chapters_doc_ordinal_unique"),
    )


class Chunk(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chunks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    heading_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="chunks")
    chapter: Mapped[Chapter | None] = relationship("Chapter", back_populates="chunks")

    __table_args__ = (
        CheckConstraint("ordinal >= 0", name="chunks_ordinal_check"),
        CheckConstraint("page_start >= 1", name="chunks_page_start_check"),
        CheckConstraint("page_end >= page_start", name="chunks_page_range_check"),
        CheckConstraint("token_count > 0", name="chunks_token_count_check"),
        UniqueConstraint("document_id", "ordinal", name="chunks_doc_ordinal_unique"),
    )


class IngestionJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ingestion_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus, name="ingestion_status"),
        nullable=False,
        default=IngestionStatus.QUEUED,
    )
    progress_pct: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    stage_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="jobs")

    __table_args__ = (
        CheckConstraint("progress_pct >= 0 AND progress_pct <= 100", name="ingestion_jobs_progress_check"),
        CheckConstraint("attempt_count >= 0", name="ingestion_jobs_attempts_check"),
        UniqueConstraint("user_id", "idempotency_key", name="ingestion_jobs_user_idempotency_unique"),
    )
