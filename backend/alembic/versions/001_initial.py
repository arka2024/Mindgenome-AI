"""001_initial: Full baseline schema matching 001_initial_schema.sql

Revision ID: 001_initial
Revises: None
Create Date: 2026-11-23 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions (PostgreSQL only)
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
        op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')

    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "disabled", "deleted", name="user_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="users_email_live_unique"),
    )
    op.create_index("users_status_idx", "users", ["status"])

    # 2. user_roles
    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.Enum("user", "admin", name="user_role"), primary_key=True, server_default="user"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. oauth_accounts
    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Enum("password", "google", name="auth_provider"), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("provider", "provider_subject", name="oauth_accounts_provider_sub_unique"),
    )
    op.create_index("oauth_accounts_user_idx", "oauth_accounts", ["user_id"])

    # 4. refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("refresh_tokens.id"), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("token_hash", name="refresh_tokens_hash_unique"),
    )
    op.create_index("refresh_tokens_user_live_idx", "refresh_tokens", ["user_id", "expires_at"])

    # 5. password_reset_tokens
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("token_hash", name="password_reset_tokens_hash_unique"),
    )
    op.create_index("password_reset_tokens_user_idx", "password_reset_tokens", ["user_id"])

    # 6. email_verification_tokens
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("token_hash", name="email_verification_tokens_hash_unique"),
    )
    op.create_index("email_verification_tokens_user_idx", "email_verification_tokens", ["user_id"])

    # 7. email_outbox
    op.create_table(
        "email_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("email_type", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "sent", "failed", name="outbox_status"),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("email_outbox_status_idx", "email_outbox", ["status"])

    # 8. documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("uploaded", "processing", "ready", "failed", "rejected", name="document_status"),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("is_low_text", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("low_text_warning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("byte_size > 0 AND byte_size <= 26214400", name="documents_byte_size_check"),
        sa.UniqueConstraint("user_id", "sha256", name="documents_user_sha_unique"),
    )
    op.create_index("documents_user_status_idx", "documents", ["user_id", "status"])

    # 9. chapters
    op.create_table(
        "chapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("start_page", sa.Integer(), nullable=False),
        sa.Column("end_page", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("ordinal >= 0", name="chapters_ordinal_check"),
        sa.CheckConstraint("start_page >= 1", name="chapters_start_page_check"),
        sa.CheckConstraint("end_page >= start_page", name="chapters_end_page_check"),
        sa.UniqueConstraint("document_id", "ordinal", name="chapters_doc_ordinal_unique"),
    )
    op.create_index("chapters_user_doc_idx", "chapters", ["user_id", "document_id"])

    # 10. chunks
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("heading_path", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("qdrant_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("ordinal >= 0", name="chunks_ordinal_check"),
        sa.CheckConstraint("page_start >= 1", name="chunks_page_start_check"),
        sa.CheckConstraint("page_end >= page_start", name="chunks_page_end_check"),
        sa.CheckConstraint("token_count > 0", name="chunks_token_count_check"),
        sa.UniqueConstraint("document_id", "ordinal", name="chunks_doc_ordinal_unique"),
    )
    op.create_index("chunks_user_doc_idx", "chunks", ["user_id", "document_id"])
    op.create_index("chunks_user_id_idx", "chunks", ["user_id"])

    # 11. ingestion_jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "parsing", "chunking", "embedding", "extracting", "graph_built", "ready", "failed",
                name="ingestion_status",
            ),
            server_default="queued",
            nullable=False,
        ),
        sa.Column("progress_pct", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("stage_detail", sa.Text(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("celery_task_id", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("progress_pct >= 0 AND progress_pct <= 100", name="ingestion_jobs_progress_check"),
        sa.CheckConstraint("attempt_count >= 0", name="ingestion_jobs_attempt_check"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="ingestion_jobs_user_idempotency_unique"),
    )
    op.create_index("ingestion_jobs_user_status_idx", "ingestion_jobs", ["user_id", "status"])
    op.create_index("ingestion_jobs_document_idx", "ingestion_jobs", ["document_id"])

    # 12. concepts
    op.create_table(
        "concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("canonical_name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("lemma", sa.Text(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "normalized_name", name="concepts_user_normalized_unique"),
    )
    op.create_index("concepts_user_lemma_idx", "concepts", ["user_id", "lemma"])

    # 13. questions
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("choices", postgresql.JSONB(), nullable=False),
        sa.Column("correct_index", sa.SmallInteger(), nullable=False),
        sa.Column("difficulty", sa.Enum("easy", "medium", "hard", name="question_difficulty"), nullable=False),
        sa.Column("quality", sa.Enum("draft", "validated", "rejected_duplicate", "rejected_invalid", name="question_quality"), server_default="draft", nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("correct_index >= 0", name="questions_correct_index_check"),
        sa.UniqueConstraint("user_id", "fingerprint", name="questions_user_fingerprint_unique"),
    )
    op.create_index("questions_user_quality_idx", "questions", ["user_id", "quality"])

    # 14. question_concepts
    op.create_table(
        "question_concepts",
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("question_concepts_user_concept_idx", "question_concepts", ["user_id", "concept_id"])

    # 15. learning_sessions
    op.create_table(
        "learning_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mode", sa.Enum("learn", "remedial", "revision", name="session_mode"), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "completed", "abandoned", name="session_status"), server_default="active", nullable=False),
        sa.Column("current_concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=True),
        sa.Column("path_json", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("learning_sessions_user_status_idx", "learning_sessions", ["user_id", "status"])

    # 16. quiz_attempts
    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_sessions.id"), nullable=True),
        sa.Column("status", sa.Enum("in_progress", "submitted", "abandoned", name="attempt_status"), server_default="in_progress", nullable=False),
        sa.Column("target_concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("quiz_attempts_user_started_idx", "quiz_attempts", ["user_id", "started_at"])

    # 17. attempt_answers
    op.create_table(
        "attempt_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("selected_index", sa.SmallInteger(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_ms", sa.Integer(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("selected_index >= 0", name="attempt_answers_selected_index_check"),
        sa.UniqueConstraint("attempt_id", "question_id", name="attempt_answers_unique_question"),
    )
    op.create_index("attempt_answers_user_time_idx", "attempt_answers", ["user_id", "answered_at"])

    # 18. mastery_scores
    op.create_table(
        "mastery_scores",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), primary_key=True),
        sa.Column("quiz_accuracy", sa.Numeric(5, 2), nullable=False),
        sa.Column("recent_performance", sa.Numeric(5, 2), nullable=False),
        sa.Column("difficulty_adjusted", sa.Numeric(5, 2), nullable=False),
        sa.Column("retention", sa.Numeric(5, 2), nullable=False),
        sa.Column("mastery", sa.Numeric(5, 2), nullable=False),
        sa.Column("band", sa.Enum("insufficient_evidence", "beginner", "developing", "proficient", "mastered", name="mastery_band"), nullable=False),
        sa.Column("evidence_n", sa.Integer(), nullable=False),
        sa.Column("component_trace", postgresql.JSONB(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quiz_accuracy BETWEEN 0 AND 100", name="mastery_scores_accuracy_check"),
        sa.CheckConstraint("recent_performance BETWEEN 0 AND 100", name="mastery_scores_recent_check"),
        sa.CheckConstraint("difficulty_adjusted BETWEEN 0 AND 100", name="mastery_scores_diff_check"),
        sa.CheckConstraint("retention BETWEEN 0 AND 100", name="mastery_scores_retention_check"),
        sa.CheckConstraint("mastery BETWEEN 0 AND 100", name="mastery_scores_mastery_check"),
        sa.CheckConstraint("evidence_n >= 0", name="mastery_scores_evidence_check"),
    )
    op.create_index("mastery_scores_user_band_idx", "mastery_scores", ["user_id", "band"])

    # 19. mastery_history
    op.create_table(
        "mastery_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("quiz_accuracy", sa.Numeric(5, 2), nullable=False),
        sa.Column("recent_performance", sa.Numeric(5, 2), nullable=False),
        sa.Column("difficulty_adjusted", sa.Numeric(5, 2), nullable=False),
        sa.Column("retention", sa.Numeric(5, 2), nullable=False),
        sa.Column("mastery", sa.Numeric(5, 2), nullable=False),
        sa.Column("band", sa.Enum("insufficient_evidence", "beginner", "developing", "proficient", "mastered", name="mastery_band"), nullable=False),
        sa.Column("evidence_n", sa.Integer(), nullable=False),
        sa.Column("component_trace", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Enum("quiz_submit", "retention_decay", "revision_complete", "manual_recompute", name="mastery_reason"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("mastery_history_user_concept_idx", "mastery_history", ["user_id", "concept_id", "recorded_at"])

    # 20. revision_schedule
    op.create_table(
        "revision_schedule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_days", sa.Numeric(6, 2), nullable=False),
        sa.Column("ease", sa.Numeric(4, 2), server_default="2.50", nullable=False),
        sa.Column("successful_reviews", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_result", sa.Boolean(), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("interval_days > 0", name="revision_schedule_interval_check"),
        sa.CheckConstraint("successful_reviews >= 0", name="revision_schedule_reviews_check"),
        sa.UniqueConstraint("user_id", "concept_id", name="revision_schedule_user_concept_unique"),
    )
    op.create_index("revision_schedule_due_idx", "revision_schedule", ["user_id", "due_at"])

    # 21. llm_call_logs
    op.create_table(
        "llm_call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Enum("concept_extract", "relationship_extract", "tutor_answer", "question_generate", "lesson_section", "repair_json", name="llm_purpose"), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("ok", "timeout", "rate_limited", "invalid_output", "provider_error", name="llm_call_status"), nullable=False),
        sa.Column("provider_request_id", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("llm_call_logs_user_created_idx", "llm_call_logs", ["user_id", "created_at"])
    op.create_index("llm_call_logs_purpose_status_idx", "llm_call_logs", ["purpose", "status", "created_at"])

    # 22. idempotency_keys
    op.create_table(
        "idempotency_keys",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Enable RLS on PostgreSQL
    if conn.dialect.name == "postgresql":
        rls_tables = [
            "documents", "chapters", "chunks", "ingestion_jobs", "concepts",
            "questions", "question_concepts", "learning_sessions", "quiz_attempts",
            "attempt_answers", "mastery_scores", "mastery_history", "revision_schedule",
            "llm_call_logs",
        ]
        for tbl in rls_tables:
            op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
            op.execute(
                f"CREATE POLICY tenant_isolation_{tbl} ON {tbl} "
                f"USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)"
            )


def downgrade() -> None:
    tables = [
        "idempotency_keys", "llm_call_logs", "revision_schedule", "mastery_history",
        "mastery_scores", "attempt_answers", "quiz_attempts", "learning_sessions",
        "question_concepts", "questions", "concepts", "ingestion_jobs", "chunks",
        "chapters", "documents", "email_outbox", "email_verification_tokens",
        "password_reset_tokens", "refresh_tokens", "oauth_accounts", "user_roles", "users",
    ]
    for tbl in tables:
        op.drop_table(tbl)
