-- MindGenome AI — PostgreSQL 16 system of record
-- Applied in Sprint 1 as Alembic revision 001_initial.
-- Soft-delete: deleted_at IS NULL means live. Queries in repositories must
-- include that predicate unless explicitly reading trash.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

CREATE TYPE user_status AS ENUM ('active', 'disabled', 'deleted');
CREATE TYPE auth_provider AS ENUM ('password', 'google');
CREATE TYPE document_status AS ENUM (
    'uploaded', 'processing', 'ready', 'failed', 'rejected'
);
CREATE TYPE ingestion_status AS ENUM (
    'queued',
    'parsing',
    'chunking',
    'embedding',
    'extracting',
    'graph_built',
    'ready',
    'failed'
);
CREATE TYPE question_difficulty AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE question_quality AS ENUM (
    'draft', 'validated', 'rejected_duplicate', 'rejected_invalid'
);
CREATE TYPE attempt_status AS ENUM (
    'in_progress', 'submitted', 'abandoned'
);
CREATE TYPE mastery_band AS ENUM (
    'insufficient_evidence',
    'beginner',
    'developing',
    'proficient',
    'mastered'
);
CREATE TYPE mastery_reason AS ENUM (
    'quiz_submit',
    'retention_decay',
    'revision_complete',
    'manual_recompute'
);
CREATE TYPE session_mode AS ENUM ('learn', 'remedial', 'revision');
CREATE TYPE session_status AS ENUM (
    'active', 'paused', 'completed', 'abandoned'
);
CREATE TYPE llm_purpose AS ENUM (
    'concept_extract',
    'relationship_extract',
    'tutor_answer',
    'question_generate',
    'lesson_section',
    'repair_json'
);
CREATE TYPE llm_call_status AS ENUM (
    'ok', 'timeout', 'rate_limited', 'invalid_output', 'provider_error'
);
CREATE TYPE user_role AS ENUM ('user', 'admin');

-- ---------------------------------------------------------------------------
-- Updated-at trigger
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------------
-- Identity
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email           citext NOT NULL,
    password_hash   text,
    display_name    text NOT NULL,
    status          user_status NOT NULL DEFAULT 'active',
    email_verified_at timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    CONSTRAINT users_email_live_unique UNIQUE (email)
);

CREATE INDEX users_status_idx ON users (status) WHERE deleted_at IS NULL;

CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE user_roles (
    user_id     uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role        user_role NOT NULL DEFAULT 'user',
    granted_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role)
);

CREATE TABLE oauth_accounts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    provider        auth_provider NOT NULL,
    provider_subject text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT oauth_accounts_provider_sub_unique UNIQUE (provider, provider_subject)
);

CREATE INDEX oauth_accounts_user_idx ON oauth_accounts (user_id);

CREATE TABLE refresh_tokens (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash      text NOT NULL,
    expires_at      timestamptz NOT NULL,
    revoked_at      timestamptz,
    replaced_by_id  uuid REFERENCES refresh_tokens (id),
    user_agent      text,
    ip_address      inet,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT refresh_tokens_hash_unique UNIQUE (token_hash)
);

CREATE INDEX refresh_tokens_user_live_idx
    ON refresh_tokens (user_id, expires_at)
    WHERE revoked_at IS NULL;

-- ---------------------------------------------------------------------------
-- Documents and ingestion
-- ---------------------------------------------------------------------------

CREATE TABLE documents (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    filename        text NOT NULL,
    content_type    text NOT NULL,
    byte_size       bigint NOT NULL CHECK (byte_size > 0 AND byte_size <= 26214400),
    storage_key     text NOT NULL,
    sha256          char(64) NOT NULL,
    status          document_status NOT NULL DEFAULT 'uploaded',
    page_count      integer,
    is_low_text     boolean NOT NULL DEFAULT false,
    low_text_warning text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    CONSTRAINT documents_user_sha_unique UNIQUE (user_id, sha256)
);

CREATE INDEX documents_user_status_idx
    ON documents (user_id, status)
    WHERE deleted_at IS NULL;

CREATE TRIGGER documents_set_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE chapters (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    document_id     uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    title           text NOT NULL,
    ordinal         integer NOT NULL CHECK (ordinal >= 0),
    start_page      integer NOT NULL CHECK (start_page >= 1),
    end_page        integer NOT NULL CHECK (end_page >= start_page),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    CONSTRAINT chapters_doc_ordinal_unique UNIQUE (document_id, ordinal)
);

CREATE INDEX chapters_user_doc_idx ON chapters (user_id, document_id);

CREATE TRIGGER chapters_set_updated_at
    BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE chunks (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    document_id     uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chapter_id      uuid REFERENCES chapters (id) ON DELETE SET NULL,
    ordinal         integer NOT NULL CHECK (ordinal >= 0),
    page_start      integer NOT NULL CHECK (page_start >= 1),
    page_end        integer NOT NULL CHECK (page_end >= page_start),
    heading_path    text,
    body            text NOT NULL,
    token_count     integer NOT NULL CHECK (token_count > 0),
    qdrant_point_id uuid,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    CONSTRAINT chunks_doc_ordinal_unique UNIQUE (document_id, ordinal)
);

CREATE INDEX chunks_user_doc_idx ON chunks (user_id, document_id);
CREATE INDEX chunks_user_id_idx ON chunks (user_id);

CREATE TRIGGER chunks_set_updated_at
    BEFORE UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE ingestion_jobs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    document_id     uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    status          ingestion_status NOT NULL DEFAULT 'queued',
    progress_pct    smallint NOT NULL DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
    stage_detail    text,
    error_code      text,
    error_message   text,
    idempotency_key text NOT NULL,
    celery_task_id  text,
    attempt_count   integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    started_at      timestamptz,
    finished_at     timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ingestion_jobs_user_idempotency_unique UNIQUE (user_id, idempotency_key)
);

CREATE INDEX ingestion_jobs_user_status_idx ON ingestion_jobs (user_id, status);
CREATE INDEX ingestion_jobs_document_idx ON ingestion_jobs (document_id);

CREATE TRIGGER ingestion_jobs_set_updated_at
    BEFORE UPDATE ON ingestion_jobs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- Concepts and questions (learner-visible content)
-- ---------------------------------------------------------------------------

CREATE TABLE concepts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    canonical_name  text NOT NULL,
    normalized_name text NOT NULL,
    lemma           text NOT NULL,
    definition      text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    CONSTRAINT concepts_user_normalized_unique UNIQUE (user_id, normalized_name)
);

CREATE INDEX concepts_user_lemma_idx ON concepts (user_id, lemma);

CREATE TRIGGER concepts_set_updated_at
    BEFORE UPDATE ON concepts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE questions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    stem            text NOT NULL,
    choices         jsonb NOT NULL,
    correct_index   smallint NOT NULL CHECK (correct_index >= 0),
    difficulty      question_difficulty NOT NULL,
    quality         question_quality NOT NULL DEFAULT 'draft',
    prompt_version  text NOT NULL,
    fingerprint     text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    CONSTRAINT questions_choices_is_array CHECK (jsonb_typeof(choices) = 'array'),
    CONSTRAINT questions_user_fingerprint_unique UNIQUE (user_id, fingerprint)
);

CREATE INDEX questions_user_quality_idx ON questions (user_id, quality);

CREATE TRIGGER questions_set_updated_at
    BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE question_concepts (
    question_id     uuid NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    concept_id      uuid NOT NULL REFERENCES concepts (id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES users (id),
    is_primary      boolean NOT NULL DEFAULT false,
    PRIMARY KEY (question_id, concept_id)
);

CREATE INDEX question_concepts_user_concept_idx
    ON question_concepts (user_id, concept_id);

-- ---------------------------------------------------------------------------
-- Learning runtime
-- ---------------------------------------------------------------------------

CREATE TABLE learning_sessions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    mode            session_mode NOT NULL,
    status          session_status NOT NULL DEFAULT 'active',
    current_concept_id uuid REFERENCES concepts (id),
    path_json       jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    ended_at        timestamptz,
    deleted_at      timestamptz
);

CREATE INDEX learning_sessions_user_status_idx
    ON learning_sessions (user_id, status)
    WHERE deleted_at IS NULL;

CREATE TRIGGER learning_sessions_set_updated_at
    BEFORE UPDATE ON learning_sessions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE quiz_attempts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    session_id      uuid REFERENCES learning_sessions (id),
    status          attempt_status NOT NULL DEFAULT 'in_progress',
    target_concept_id uuid REFERENCES concepts (id),
    started_at      timestamptz NOT NULL DEFAULT now(),
    submitted_at    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz
);

CREATE INDEX quiz_attempts_user_started_idx ON quiz_attempts (user_id, started_at DESC);

CREATE TRIGGER quiz_attempts_set_updated_at
    BEFORE UPDATE ON quiz_attempts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE attempt_answers (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    attempt_id      uuid NOT NULL REFERENCES quiz_attempts (id) ON DELETE CASCADE,
    question_id     uuid NOT NULL REFERENCES questions (id),
    selected_index  smallint NOT NULL CHECK (selected_index >= 0),
    is_correct      boolean NOT NULL,
    time_ms         integer CHECK (time_ms IS NULL OR time_ms >= 0),
    answered_at     timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT attempt_answers_unique_question UNIQUE (attempt_id, question_id)
);

CREATE INDEX attempt_answers_user_time_idx ON attempt_answers (user_id, answered_at);

CREATE TABLE mastery_scores (
    user_id         uuid NOT NULL REFERENCES users (id),
    concept_id      uuid NOT NULL REFERENCES concepts (id),
    quiz_accuracy   numeric(5,2) NOT NULL CHECK (quiz_accuracy BETWEEN 0 AND 100),
    recent_performance numeric(5,2) NOT NULL CHECK (recent_performance BETWEEN 0 AND 100),
    difficulty_adjusted numeric(5,2) NOT NULL CHECK (difficulty_adjusted BETWEEN 0 AND 100),
    retention       numeric(5,2) NOT NULL CHECK (retention BETWEEN 0 AND 100),
    mastery         numeric(5,2) NOT NULL CHECK (mastery BETWEEN 0 AND 100),
    band            mastery_band NOT NULL,
    evidence_n      integer NOT NULL CHECK (evidence_n >= 0),
    component_trace jsonb NOT NULL,
    computed_at     timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, concept_id)
);

CREATE INDEX mastery_scores_user_band_idx ON mastery_scores (user_id, band);

CREATE TRIGGER mastery_scores_set_updated_at
    BEFORE UPDATE ON mastery_scores
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE mastery_history (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    concept_id      uuid NOT NULL REFERENCES concepts (id),
    quiz_accuracy   numeric(5,2) NOT NULL,
    recent_performance numeric(5,2) NOT NULL,
    difficulty_adjusted numeric(5,2) NOT NULL,
    retention       numeric(5,2) NOT NULL,
    mastery         numeric(5,2) NOT NULL,
    band            mastery_band NOT NULL,
    evidence_n      integer NOT NULL,
    component_trace jsonb NOT NULL,
    reason          mastery_reason NOT NULL,
    recorded_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX mastery_history_user_concept_idx
    ON mastery_history (user_id, concept_id, recorded_at DESC);

CREATE TABLE revision_schedule (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users (id),
    concept_id      uuid NOT NULL REFERENCES concepts (id),
    due_at          timestamptz NOT NULL,
    interval_days   numeric(6,2) NOT NULL CHECK (interval_days > 0),
    ease            numeric(4,2) NOT NULL DEFAULT 2.50,
    successful_reviews integer NOT NULL DEFAULT 0 CHECK (successful_reviews >= 0),
    last_result     boolean,
    last_reviewed_at timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT revision_schedule_user_concept_unique UNIQUE (user_id, concept_id)
);

CREATE INDEX revision_schedule_due_idx ON revision_schedule (user_id, due_at);

CREATE TRIGGER revision_schedule_set_updated_at
    BEFORE UPDATE ON revision_schedule
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- LLM audit
-- ---------------------------------------------------------------------------

CREATE TABLE llm_call_logs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES users (id),
    prompt_version  text NOT NULL,
    model           text NOT NULL,
    purpose         llm_purpose NOT NULL,
    input_tokens    integer,
    output_tokens   integer,
    cost_usd        numeric(10,6),
    latency_ms      integer,
    status          llm_call_status NOT NULL,
    provider_request_id text,
    error_message   text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX llm_call_logs_user_created_idx ON llm_call_logs (user_id, created_at DESC);
CREATE INDEX llm_call_logs_purpose_status_idx ON llm_call_logs (purpose, status, created_at DESC);

CREATE TABLE idempotency_keys (
    user_id         uuid NOT NULL REFERENCES users (id),
    key             text NOT NULL,
    method          text NOT NULL,
    path            text NOT NULL,
    request_hash    text NOT NULL,
    response_status integer NOT NULL,
    response_body   jsonb NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL,
    PRIMARY KEY (user_id, key)
);

-- ---------------------------------------------------------------------------
-- Row Level Security (defense in depth; app still binds user_id)
-- Session GUC: SET app.current_user_id = '<uuid>';
-- ---------------------------------------------------------------------------

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE attempt_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE mastery_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE mastery_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE revision_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_call_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_documents ON documents
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_chapters ON chapters
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_chunks ON chunks
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_ingestion_jobs ON ingestion_jobs
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_concepts ON concepts
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_questions ON questions
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_question_concepts ON question_concepts
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_learning_sessions ON learning_sessions
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_quiz_attempts ON quiz_attempts
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_attempt_answers ON attempt_answers
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_mastery_scores ON mastery_scores
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_mastery_history ON mastery_history
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_revision_schedule ON revision_schedule
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
CREATE POLICY tenant_isolation_llm_call_logs ON llm_call_logs
    USING (user_id IS NULL OR user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);
