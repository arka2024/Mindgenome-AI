from __future__ import annotations

import enum


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class AuthProvider(str, enum.Enum):
    PASSWORD = "password"
    GOOGLE = "google"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    REJECTED = "rejected"


class IngestionStatus(str, enum.Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    EXTRACTING = "extracting"
    GRAPH_BUILT = "graph_built"
    READY = "ready"
    FAILED = "failed"


class QuestionDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionQuality(str, enum.Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_INVALID = "rejected_invalid"


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"


class MasteryBand(str, enum.Enum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class MasteryReason(str, enum.Enum):
    QUIZ_SUBMIT = "quiz_submit"
    RETENTION_DECAY = "retention_decay"
    REVISION_COMPLETE = "revision_complete"
    MANUAL_RECOMPUTE = "manual_recompute"


class SessionMode(str, enum.Enum):
    LEARN = "learn"
    REMEDIAL = "remedial"
    REVISION = "revision"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class LLMPurpose(str, enum.Enum):
    CONCEPT_EXTRACT = "concept_extract"
    RELATIONSHIP_EXTRACT = "relationship_extract"
    TUTOR_ANSWER = "tutor_answer"
    QUESTION_GENERATE = "question_generate"
    LESSON_SECTION = "lesson_section"
    REPAIR_JSON = "repair_json"


class LLMCallStatus(str, enum.Enum):
    OK = "ok"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    INVALID_OUTPUT = "invalid_output"
    PROVIDER_ERROR = "provider_error"


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
