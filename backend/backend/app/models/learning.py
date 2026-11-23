from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import (
    AttemptStatus,
    MasteryBand,
    MasteryReason,
    QuestionDifficulty,
    QuestionQuality,
    SessionMode,
    SessionStatus,
)


class Concept(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "concepts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)
    lemma: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name", name="concepts_user_normalized_unique"),
    )


class Question(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "questions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    correct_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    difficulty: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty, name="question_difficulty"),
        nullable=False,
    )
    quality: Mapped[QuestionQuality] = mapped_column(
        Enum(QuestionQuality, name="question_quality"),
        default=QuestionQuality.DRAFT,
        nullable=False,
        index=True,
    )
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)

    concepts: Mapped[list[QuestionConcept]] = relationship(
        "QuestionConcept",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("correct_index >= 0", name="questions_correct_index_check"),
        UniqueConstraint("user_id", "fingerprint", name="questions_user_fingerprint_unique"),
    )


class QuestionConcept(Base):
    __tablename__ = "question_concepts"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    question: Mapped[Question] = relationship("Question", back_populates="concepts")
    concept: Mapped[Concept] = relationship("Concept")


class LearningSession(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "learning_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[SessionMode] = mapped_column(
        Enum(SessionMode, name="session_mode"),
        nullable=False,
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    current_concept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
    )
    path_json: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    concept: Mapped[Concept | None] = relationship("Concept")


class QuizAttempt(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "quiz_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status"),
        default=AttemptStatus.IN_PROGRESS,
        nullable=False,
    )
    target_concept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list[AttemptAnswer]] = relationship(
        "AttemptAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    target_concept: Mapped[Concept | None] = relationship("Concept")


class AttemptAnswer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attempt_answers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    selected_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    attempt: Mapped[QuizAttempt] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped[Question] = relationship("Question")

    __table_args__ = (
        CheckConstraint("selected_index >= 0", name="attempt_answers_selected_index_check"),
        CheckConstraint("time_ms IS NULL OR time_ms >= 0", name="attempt_answers_time_ms_check"),
        UniqueConstraint("attempt_id", "question_id", name="attempt_answers_unique_question"),
    )


class MasteryScore(Base, TimestampMixin):
    __tablename__ = "mastery_scores"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    quiz_accuracy: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    recent_performance: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    difficulty_adjusted: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    retention: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    mastery: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    band: Mapped[MasteryBand] = mapped_column(
        Enum(MasteryBand, name="mastery_band"),
        nullable=False,
        index=True,
    )
    evidence_n: Mapped[int] = mapped_column(Integer, nullable=False)
    component_trace: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    concept: Mapped[Concept] = relationship("Concept")

    __table_args__ = (
        CheckConstraint("quiz_accuracy >= 0 AND quiz_accuracy <= 100", name="mastery_quiz_acc_check"),
        CheckConstraint("recent_performance >= 0 AND recent_performance <= 100", name="mastery_recent_perf_check"),
        CheckConstraint("difficulty_adjusted >= 0 AND difficulty_adjusted <= 100", name="mastery_dap_check"),
        CheckConstraint("retention >= 0 AND retention <= 100", name="mastery_retention_check"),
        CheckConstraint("mastery >= 0 AND mastery <= 100", name="mastery_score_check"),
        CheckConstraint("evidence_n >= 0", name="mastery_evidence_check"),
    )


class MasteryHistory(Base, UUIDMixin):
    __tablename__ = "mastery_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quiz_accuracy: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    recent_performance: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    difficulty_adjusted: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    retention: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    mastery: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    band: Mapped[MasteryBand] = mapped_column(
        Enum(MasteryBand, name="mastery_band"),
        nullable=False,
    )
    evidence_n: Mapped[int] = mapped_column(Integer, nullable=False)
    component_trace: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    reason: Mapped[MasteryReason] = mapped_column(
        Enum(MasteryReason, name="mastery_reason"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


class RevisionSchedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "revision_schedule"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    interval_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    ease: Mapped[float] = mapped_column(Numeric(4, 2), default=2.50, nullable=False)
    successful_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    concept: Mapped[Concept] = relationship("Concept")

    __table_args__ = (
        CheckConstraint("interval_days > 0", name="revision_interval_check"),
        CheckConstraint("successful_reviews >= 0", name="revision_success_check"),
        UniqueConstraint("user_id", "concept_id", name="revision_schedule_user_concept_unique"),
    )
