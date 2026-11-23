# MindGenome AI — Complete Technical Backend Audit & Implementation Roadmap

**Date:** November 23, 2026  
**Auditor:** Senior Backend Architect, Senior Python Engineer, Database & AI Systems Engineer  
**Audit Target:** `Mindgenome-AI-main`  
**Current State:** Phase 0 Architecture & Approved Design Artifacts (Pre-Sprint 1)  
**Target State:** Production-Ready, Secure, Scalable Backend (PostgreSQL 16, FastAPI, Celery, Redis, Qdrant, Neo4j, Gemini API, S3/MinIO)

---

## 1. Executive Summary

A comprehensive technical audit of the `Mindgenome-AI-main` repository was conducted. 

### Key Findings
1. **Application Code Status:** The backend application code has **not yet been implemented** in Python. The repository is currently frozen at **Phase 0** ("Approved design artifacts"). As explicitly documented in `README.md`, application code was slated to begin in Sprint 1.
2. **No Legacy Technical Debt in Code:** There is **no existing SQLite code**, **no bloated `main.py`**, and **no legacy SQLAlchemy models** that need to be torn down. The codebase is a pristine greenfield implementation opportunity governed by strict, high-quality architectural specifications.
3. **Architectural Blueprints are Mature:** Complete PostgreSQL 16 DDL (`docs/data/001_initial_schema.sql`), Neo4j Cypher constraints and queries (`docs/data/neo4j_*.cypher`), OpenAPI 3.1 specification (`docs/openapi/openapi.yaml`), Mastery engine mathematical formulas (`docs/MASTERY.md`), Graph-Augmented RAG retrieval algorithms (`docs/QDRANT.md`), and 14 Architecture Decision Records (`docs/adr/`) already exist and are approved.
4. **Frontend is Fully Implemented:** A complete React 18 + TypeScript + Tailwind CSS + Cytoscape.js single-page application exists in `frontend/`, currently powered by Mock Service Worker (MSW) in `frontend/src/mocks/`. It specifies the exact frontend expectation of every HTTP endpoint, payload, and status code.
5. **Contract Discrepancies Identified:** Crucial endpoint discrepancies were discovered between `frontend/src/features/auth/AuthPages.tsx` (which calls `/auth/forgot`), `frontend/src/mocks/handlers.ts`, OpenAPI specifications, and the prompt pack requirements (`/auth/forgot-password` and `/auth/reset-password`). These have been cataloged and reconciled in this audit.

---

## 2. Detailed Technical Audit

### 2.1 Directory & File Structure

```
Mindgenome-AI-main/
├── .env.example                     # Environment variable blueprint (12-factor)
├── .gitignore                       # Standard Git exclusions
├── README.md                        # Phase 0 summary & decisions
├── docs/                            # Architectural specifications
│   ├── API.md                       # REST conventions & endpoint table
│   ├── ARCHITECTURE.md              # C4 models, sequences, package layout, SoT rules
│   ├── CONTRIBUTING.md              # Development rules & commit conventions
│   ├── DELIVERY.md                  # Environments, CI/CD, deployment costing
│   ├── DESIGN.md                    # Learning science & product design
│   ├── FRONTEND.md                  # Routing, state management, accessibility
│   ├── GRAPH.md                     # Neo4j knowledge graph schema & relationships
│   ├── MASTERY.md                   # Exact mastery scoring formulas & decay rules
│   ├── QDRANT.md                    # Vector collections, chunking, MMR retrieval
│   ├── SECURITY.md                  # Threat model, auth, upload hygiene, prompt injection
│   ├── adr/                         # 14 Architecture Decision Records (ADR-001 to ADR-014)
│   ├── data/
│   │   ├── 001_initial_schema.sql   # PostgreSQL 16 DDL (15 tables, 14 enums, triggers, RLS)
│   │   ├── neo4j_constraints.cypher # Neo4j unique constraints & indexes
│   │   └── neo4j_queries.cypher     # Parametric Cypher queries for traversal & cycles
│   └── openapi/
│       └── openapi.yaml             # OpenAPI 3.1 contract (22 endpoints)
├── frontend/                        # Production React + TS + Tailwind SPA
│   ├── src/
│   │   ├── api/                     # Typed client (client.ts), Zod schemas (schemas.ts)
│   │   ├── features/                # auth, dashboard, documents, graph, learning, mastery, tutor, quiz
│   │   ├── mocks/                   # MSW browser/server mocks, in-memory store, seed curriculum
│   │   └── shared/                  # UI components, layout shell, helpers
│   ├── package.json                 # React 18, Vite 5, Tailwind 3.4, Cytoscape 3.30
├── infra/
│   └── render.yaml                  # Render PaaS blueprint (API, Celery worker, datastores)
├── scripts/
│   └── validate_phase0.py           # Verification script for Phase 0 artifacts
└── tests/
    └── test_phase0_artifacts.py     # Pytest test asserting Phase 0 validity
```

---

### 2.2 Verification of Known Issues & Assumptions

| Known Issue to Verify | Status | Audit Finding |
|---|---|---|
| **Current implementation uses SQLite** | **Negative** | No SQLite implementation exists. There is no existing Python database code. PostgreSQL 16 was selected as the system of record from day one. |
| **Database migrations are missing** | **Confirmed** | Alembic has not yet been initialized. `001_initial_schema.sql` exists as raw SQL DDL and must be converted into the first Alembic migration (`001_initial`). |
| **Too much logic in `main.py`** | **Negative** | No `main.py` exists yet. We will build a modular architecture immediately in accordance with `docs/ARCHITECTURE.md`. |
| **Refresh-token reuse detection missing** | **Confirmed** | Not implemented yet in code. The database schema in `001_initial_schema.sql` already has `refresh_tokens.token_hash`, `replaced_by_id`, and `revoked_at` ready for this logic. |
| **Google OAuth validation issues** | **Confirmed** | No OAuth handling exists. Must implement authorization code flow with PKCE, validating token signature, issuer (`https://accounts.google.com`), audience (`GOOGLE_OAUTH_CLIENT_ID`), expiration, and `email_verified == true`. |
| **Account linking security risks** | **Confirmed** | Must enforce rule from `docs/SECURITY.md`: automatically link only if Google email matches an existing verified account. If unverified, require password login first. |
| **Email verification race conditions** | **Confirmed** | No email verification implemented. We will implement a transactional outbox pattern to guarantee atomic account creation and email queueing. |
| **Password reset missing in API** | **Confirmed Discrepancy** | Frontend calls `POST /auth/forgot`, while `openapi.yaml` lacked forgot-password routes entirely, and Prompt 2 specifies `/auth/forgot-password` and `/auth/reset-password`. We will support both paths to ensure seamless compatibility. |
| **Redis rate limiting missing** | **Confirmed** | Not implemented in code. Must implement Redis-backed sliding window / token bucket rate limiting for auth, upload, and tutor routes. |
| **Document upload & ingestion missing** | **Confirmed** | Backend APIs for PDF/DOCX upload, chunking, MinIO/S3 storage, and Celery processing do not exist. |
| **Vector & Graph retrieval missing** | **Confirmed** | Qdrant vector retrieval and Neo4j knowledge graph integration are not implemented. |
| **Tutor, Quiz, Mastery, Path APIs missing** | **Confirmed** | Not implemented. Domain logic from `docs/MASTERY.md` and `docs/GRAPH.md` must be coded as pure Python domain modules. |
| **Automated tests insufficient** | **Confirmed** | Only Phase 0 architectural assertions exist. Zero backend unit, integration, or functional tests exist. |

---

### 2.3 Database Schema & Models Audit

The database schema defined in `docs/data/001_initial_schema.sql` is exceptionally detailed and production-grade.

#### Tables (15 Total):
1. `users`: UUID primary key, `citext` email, `password_hash`, `display_name`, `status` (`user_status`), `email_verified_at`, timestamps, soft delete (`deleted_at`).
2. `user_roles`: `(user_id, role)` composite PK, role (`user`, `admin`).
3. `oauth_accounts`: Federated identity link, `(provider, provider_subject)` unique.
4. `refresh_tokens`: `token_hash` unique, `expires_at`, `revoked_at`, `replaced_by_id` self-reference for family rotation, IP and User-Agent audit fields.
5. `documents`: Storage metadata (`storage_key`, `byte_size`, `sha256`, `status`), page count, `is_low_text` warning, user tenancy.
6. `chapters`: Structural book/document navigation (`document_id`, `ordinal`, `start_page`, `end_page`).
7. `chunks`: Core text chunks (`body`, `token_count`, `qdrant_point_id`, `page_start`, `page_end`, `heading_path`).
8. `ingestion_jobs`: Celery task tracking (`status`, `progress_pct`, `stage_detail`, `error_code`, `idempotency_key`, `celery_task_id`, `attempt_count`).
9. `concepts`: Learner concepts (`canonical_name`, `normalized_name`, `lemma`, `definition`).
10. `questions`: Multiple-choice and assessment questions (`stem`, `choices` JSONB, `correct_index`, `difficulty`, `quality`, `prompt_version`, `fingerprint`).
11. `question_concepts`: Many-to-many relationship linking questions to concepts (`is_primary`).
12. `learning_sessions`: Active learning sessions (`mode`, `status`, `current_concept_id`, `path_json`).
13. `quiz_attempts`: Attempt instances (`session_id`, `status`, `target_concept_id`, `started_at`, `submitted_at`).
14. `attempt_answers`: Individual question answers (`selected_index`, `is_correct`, `time_ms`).
15. `mastery_scores`: Current mastery state (`quiz_accuracy`, `recent_performance`, `difficulty_adjusted`, `retention`, `mastery`, `band`, `evidence_n`, `component_trace` JSONB).
16. `mastery_history`: Append-only audit log of mastery evaluations (`reason`: `quiz_submit`, `retention_decay`, `revision_complete`, `manual_recompute`).
17. `revision_schedule`: Spaced repetition tracking (`due_at`, `interval_days`, `ease`, `successful_reviews`, `last_result`).
18. `llm_call_logs`: Audit trail of Gemini API calls (`model`, `purpose`, `input_tokens`, `output_tokens`, `cost_usd`, `latency_ms`, `status`).
19. `idempotency_keys`: Dedicated table for idempotent mutation replay (`user_id`, `key`, `request_hash`, `response_status`, `response_body`).

#### Security Mechanisms in Schema:
- **Row-Level Security (RLS):** Enabled on all 14 tenant-owned tables using `app.current_user_id` session setting as defense-in-depth.
- **Triggers:** Automatic `updated_at` maintenance on all mutable tables.
- **Data Integrity:** Check constraints on percentage bounds, positive byte counts, array types, and uniqueness constraints.

---

### 2.4 API Surface & Frontend Integration Mapping

To guarantee that the backend works out of the box with the existing frontend SPA, we cross-referenced all endpoints:

| Method | Endpoint | Required by Frontend | Defined in OpenAPI | Scope in Prompt Pack | Action Required |
|---|---|---|---|---|---|
| `GET` | `/health` | Yes | Yes | Phase 5 | Implement liveness probe |
| `GET` | `/ready` | Yes | Yes | Phase 5 | Implement readiness probe (Postgres, Redis, Qdrant, Neo4j, S3) |
| `POST` | `/auth/register` | Yes | Yes | Phase 1 | User registration with Argon2id |
| `POST` | `/auth/login` | Yes | Yes | Phase 1 | Email/password login → TokenPair |
| `POST` | `/auth/refresh` | Yes | Yes | Phase 1 | Rotating refresh token |
| `POST` | `/auth/logout` | Yes | Yes | Phase 1 | Revoke token family |
| `GET` | `/auth/me` | Yes | Yes | Phase 1 | Current user info |
| `GET` | `/auth/google/start` | Yes | Yes | Phase 1 | Redirect to Google OAuth URL |
| `GET` | `/auth/google/callback` | Yes | Yes | Phase 1 | Code exchange & token issuance |
| `POST` | `/auth/forgot` | **Yes (Frontend UI)** | *Missing in OpenAPI* | Phase 1 | **Must implement** to support frontend recovery |
| `POST` | `/auth/forgot-password` | Prompt 2 | *Missing in OpenAPI* | Phase 1 | Alias to `/auth/forgot` |
| `POST` | `/auth/reset-password` | Prompt 2 | *Missing in OpenAPI* | Phase 1 | Reset password with token |
| `POST` | `/auth/verify-email` | Prompt 2 | *Missing in OpenAPI* | Phase 1 | Email verification handler |
| `POST` | `/auth/resend-verification`| Prompt 2 | *Missing in OpenAPI* | Phase 1 | Resend verification token |
| `GET` | `/documents` | Yes | Yes | Phase 2 | Paginated list of user documents |
| `POST` | `/documents` | Yes | Yes | Phase 2 | Upload PDF/DOCX + enqueue Celery job |
| `POST` | `/documents/upload` | Prompt 3 | *Alternative path* | Phase 2 | Alias to `POST /documents` |
| `GET` | `/documents/{id}` | Yes | Yes | Phase 2 | Document details + chapters |
| `DELETE`| `/documents/{id}` | Yes (Mock) | *Missing in OpenAPI* | Phase 2 | Delete document, chunks, vectors, graph nodes |
| `GET` | `/ingestion-jobs/{id}` | Yes | Yes | Phase 2 | Check ingestion status & progress |
| `GET` | `/documents/{id}/status`| Prompt 3 | *Alternative path* | Phase 2 | Document status lookup |
| `POST` | `/documents/{id}/reprocess`| Prompt 3| *Alternative path*| Phase 2 | Reprocess failed document |
| `GET` | `/graph` | Yes | Yes | Phase 3 | Cytoscape graph payload |
| `POST` | `/graph/edges/{id}/review`| Yes | Yes | Phase 3 | Confirm or reject prerequisite edge |
| `POST` | `/tutor/ask` | Yes | Yes | Phase 4 | Grounded AI tutor with citations |
| `GET` | `/chunks/{id}` | Yes (Frontend) | *Missing in OpenAPI* | Phase 3 | Fetch full passage of chunk |
| `POST` | `/learning-sessions` | Yes | Yes | Phase 4 | Start learning/remedial session |
| `GET` | `/learning-sessions/{id}`| Yes | Yes | Phase 4 | Get current session state & sections |
| `POST` | `/learning-sessions/{id}/progress`| Yes (Frontend)| *Missing in OpenAPI* | Phase 4 | Advance section / mark understood |
| `PATCH`| `/learning/sessions/{id}`| Prompt 5 | *Alternative path* | Phase 4 | Update session |
| `POST` | `/learning/sessions/{id}/complete`| Prompt 5 | *Alternative path* | Phase 4 | Mark session complete |
| `POST` | `/quizzes` | Yes (Frontend) | *Missing in OpenAPI* | Phase 4 | Alias to `POST /quiz-attempts` |
| `POST` | `/quizzes/generate` | Prompt 5 | *Alternative path* | Phase 4 | Alias / direct quiz generation |
| `POST` | `/quiz-attempts` | Yes | Yes | Phase 4 | Generate/create quiz attempt |
| `GET` | `/quiz-attempts/{id}` | Yes (Frontend) | *Missing in OpenAPI* | Phase 4 | Get quiz attempt questions |
| `POST` | `/quiz-attempts/{id}/submit`| Yes | Yes | Phase 4 | Submit answers, score, update mastery |
| `GET` | `/mastery` | Yes | Yes | Phase 4 | User concept mastery scores |
| `GET` | `/mastery/{id}` | Yes | Yes | Phase 4 | Single concept mastery trace & history |
| `GET` | `/learning-path` | Yes | Yes | Phase 4 | Recommended next concepts & remedial paths |
| `GET` | `/dashboard` | Yes | Yes | Phase 4 | Aggregated learner dashboard |

---

## 3. Recommended Backend Architecture

Following `docs/ARCHITECTURE.md` and Prompt 6, the backend should be organized as a **clean, layered modular monolith**:

```
backend/
├── pyproject.toml               # Poetry/Hatch/Pip dependencies and tool configurations
├── alembic.ini                  # Alembic database migration config
├── alembic/
│   ├── env.py                   # Async SQLAlchemy Alembic migration environment
│   └── versions/
│       └── 001_initial.py       # Full baseline migration derived from 001_initial_schema.sql
├── app/
│   ├── main.py                  # FastAPI application entrypoint, middleware, routers
│   ├── api/
│   │   ├── dependencies/        # Auth deps, DB sessions, Redis, current_user, tenant context
│   │   └── v1/                  # API routers (auth, documents, graph, tutor, learning, quizzes, mastery, dashboard)
│   ├── core/
│   │   ├── config.py            # Pydantic v2 Settings (12-factor env management)
│   │   ├── security.py          # Argon2id hashing, JWT access/refresh token helpers
│   │   ├── logging.py           # Structlog JSON configuration & correlation IDs
│   │   └── exceptions.py        # RFC 7807 Problem Details exception handlers
│   ├── db/
│   │   ├── session.py           # Async SQLAlchemy engine & async sessionmaker
│   │   └── base.py              # DeclarativeBase, Common Mixins (UUID, Timestamps, SoftDelete)
│   ├── models/                  # SQLAlchemy 2.0 ORM models (User, Document, Chunk, Attempt, Mastery, etc.)
│   ├── schemas/                 # Pydantic v2 request/response schemas & RFC 7807 problem schemas
│   ├── domain/                  # Pure business logic (no web/db frameworks):
│   │   ├── mastery.py           # Exact mastery formulas (Acc, Rec, DAP, Ret, M, Bands)
│   │   ├── path.py              # Learning path recommendation & remedial planner
│   │   └── evidence.py          # Minimum evidence (n >= 3) and confidence threshold rules
│   ├── repositories/            # Database access layer (UserRepo, DocumentRepo, MasteryRepo, etc.)
│   ├── services/                # Application orchestration use cases (AuthService, IngestionService, RAGService)
│   ├── adapters/                # External service integrations:
│   │   ├── postgres.py          # PostgreSQL session management & RLS setting
│   │   ├── neo4j.py             # Neo4j async driver wrapper & Cypher runner
│   │   ├── qdrant.py            # Qdrant client, collection setup, payload filtering
│   │   ├── gemini.py            # Gemini 2.5 Pro client with structured outputs & retries
│   │   ├── storage.py           # S3 / MinIO client (boto3 / aioboto3)
│   │   ├── redis.py             # Redis connection pool & rate limiter
│   └── workers/
│       ├── celery_app.py        # Celery application configuration & beat schedule
│       └── tasks/
│           ├── ingestion.py     # Document parsing, chunking, embedding, extraction
│           ├── decay.py         # Daily mastery retention decay job
│           └── email.py         # Outbox worker for async email delivery
│   └── prompts/                 # Versioned prompt templates (.md) and JSON schemas
├── tests/
│   ├── conftest.py              # Test fixtures (async client, test DB, mock services)
│   ├── unit/                    # Domain logic & utility tests (mastery formula, chunker, security)
│   ├── integration/             # DB & API endpoint tests with test containers / test DB
│   └── golden/                  # Document ingestion & prompt extraction test fixtures
├── Dockerfile                   # Multi-stage production Dockerfile
└── docker-compose.yml           # Complete local dev stack (FastAPI, Postgres, Redis, Celery, MinIO, Qdrant, Neo4j)
```

---

## 4. Implementation Phase Roadmap

### Phase 1: Production Authentication, Database & Security
1. Set up `pyproject.toml` with pinned, compatible dependencies (FastAPI, SQLAlchemy 2.0, Asyncpg, Alembic, Pydantic 2.x, Pwdlib/Argon2-cffi, PyJWT, Redis).
2. Configure async SQLAlchemy database connection with connection pooling and health checks.
3. Initialize Alembic and create `001_initial` migration matching `docs/data/001_initial_schema.sql`.
4. Create SQLAlchemy ORM models matching all 15 tables with relationships, indexes, and constraints.
5. Implement authentication services:
   - User registration (Argon2id password hashing).
   - Login & JWT issuance (15-min access token).
   - Refresh-token rotation: SHA-256 hashed storage, token family tracking (`replaced_by_id`), reuse detection revoking the entire family.
   - Logout (revoking token family).
   - Current user (`GET /auth/me`).
   - Password reset (`POST /auth/forgot` and `/auth/forgot-password`, `POST /auth/reset-password`).
   - Email verification with transactional outbox.
   - Google OAuth 2.0 authorization code flow with PKCE, validating `iss`, `aud`, `exp`, `email_verified`, and secure account linking.
   - Redis-backed rate limiting (5 attempts/min on auth).
6. Unit and integration tests for all auth flows.

### Phase 2: Document Management & Asynchronous Ingestion
1. Integrate S3-compatible storage adapter (AWS S3 & local MinIO).
2. Implement document upload API: `POST /documents` (multipart PDF/DOCX, magic bytes verification, 25MB cap, SHA-256 deduplication).
3. Implement document management APIs: `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}`.
4. Set up Celery with Redis broker and result backend.
5. Build document parsing and chunking pipeline:
   - PyMuPDF / python-docx text extraction.
   - Header/footer cleanup.
   - Low-text / scanned PDF detection with fail-closed warning.
   - Chapter detection and 512-token / 64-token overlap chunking.
   - Ingestion status progression (`queued` → `parsing` → `chunking` → `embedding` → `extracting` → `graph_built` → `ready`).
6. Implement `GET /ingestion-jobs/{id}` and reprocess API.
7. Unit and integration tests for document parsing, chunking, and Celery jobs.

### Phase 3: AI Infrastructure, Knowledge Graph, Vector DB & RAG
1. Implement embedding service using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
2. Integrate Qdrant vector database:
   - Collection setup (`mindgenome_chunks`, cosine distance).
   - Upsert chunk embeddings with `user_id` payload filter.
   - Vector search with mandatory `user_id` constraint.
3. Integrate Neo4j knowledge graph:
   - Run initial constraints from `docs/data/neo4j_constraints.cypher`.
   - Implement parametric queries with cycle prevention before merging `PREREQUISITE_OF` edges.
4. Integrate Gemini 2.5 Pro (Google AI Studio):
   - Structured JSON output schemas for concept extraction, edge discovery, and tutor responses.
   - Exponential backoff, timeout handling, and `llm_call_logs` auditing.
5. Implement Graph-Augmented RAG retrieval pipeline:
   - MiniLM query embedding.
   - Qdrant similarity search (top 12, cosine $\ge 0.35$).
   - PostgreSQL chunk body hydration.
   - Neo4j concept expansion (up to 4 related chunks, capped at 8).
   - Greedy MMR context fusion ($\lambda = 0.7$).
   - Confidence scoring (`high`, `medium`, `low` refusal).
6. Implement `GET /graph`, `POST /graph/edges/{id}/review`, `POST /tutor/ask`, `GET /chunks/{id}`.
7. Unit and integration tests with mocked Gemini and Qdrant/Neo4j test fixtures.

### Phase 4: Core Learning Platform Features
1. Implement Learning Sessions: `POST /learning-sessions`, `GET /learning-sessions/{id}`, `POST /learning-sessions/{id}/progress`.
2. Implement AI Tutor: Multi-turn grounded tutoring with citations and follow-up suggestions.
3. Implement Quiz Generation & Evaluation:
   - Multiple-choice questions with objective scoring.
   - `POST /quiz-attempts`, `POST /quiz-attempts/{id}/submit`.
4. Implement Mastery Engine:
   - Pure domain functions calculating $Acc$ (0.40), $Rec$ (0.20), $DAP$ (0.20), $Ret$ (0.20), and composite score $M$.
   - Evidence threshold ($n \ge 3$) before assigning non-insufficient bands.
   - Neo4j `STRUGGLES_WITH` sync when band is `beginner` and $n \ge 3$.
   - Daily Celery beat retention decay job.
5. Implement Adaptive Learning Path:
   - Neo4j weakest ancestor graph traversal for remedial path generation.
   - `GET /learning-path`.
6. Implement Dashboard Aggregator:
   - `GET /dashboard` returning overall mastery, band counts, weak concepts, recommended next step, active jobs, and revisions.
7. Comprehensive tests for mastery calculations, quiz evaluation, and data isolation.

### Phase 5: Architecture Refactoring, Observability & Production Readiness
1. Standardize RFC 7807 error responses across all routers.
2. Structured logging with Structlog (JSON format, `request_id` correlation, scrubbing tokens and secrets).
3. Health check endpoints: `GET /health` (liveness), `GET /ready` (readiness pinging Postgres, Redis, Neo4j, Qdrant, S3).
4. Containerization:
   - Production multi-stage `Dockerfile`.
   - Comprehensive `docker-compose.yml` defining FastAPI, Postgres 16, Redis, Celery Worker, MinIO, Qdrant, and Neo4j.
5. CI/CD:
   - GitHub Actions workflow running Ruff, MyPy, Pytest, and security scanners.
6. Final verification and `BACKEND_FINAL_REPORT.md`.

---

## 5. Security & Isolation Strategy

1. **Multi-Tenancy Guardrails:**
   - Every database query must bind `user_id = :current_user_id`.
   - PostgreSQL Row-Level Security (RLS) enabled on all tables as an unbypassable defense-in-depth layer.
   - Neo4j queries must bind `user_id: $user_id` on every node and relationship hop.
   - Qdrant queries must include a mandatory `must: [FieldCondition(key="user_id", match=MatchValue(value=user_id))]`.
   - Object storage keys prefixed by `users/{user_id}/documents/{document_id}/{filename}`.
2. **Cryptographic Standards:**
   - Passwords hashed with Argon2id ($t=3$, $m=64\text{ MiB}$, $p=4$).
   - Refresh tokens stored as SHA-256 hashes; plain tokens never persisted.
   - Single-use token rotation with instant family invalidation upon reuse detection.
3. **Prompt Injection Defense:**
   - Delimit untrusted document chunks with strict sentinels: `<UNTRUSTED_DOCUMENT chunk_id=...>`.
   - Structured JSON schema enforcement via Gemini API.
   - Server-side verification that returned citation chunk IDs belong to the retrieved set.
4. **Rate Limiting & Lockout:**
   - 5 requests/minute per IP on authentication routes.
   - 10 uploads/hour per user.
   - 30 questions/minute per user on tutor.

---

## 6. Testing Strategy

1. **Unit Tests (`tests/unit/`):**
   - Pure domain mastery calculations (verifying exact mathematical values from `docs/MASTERY.md`).
   - Token rotation and hash generation.
   - Chunking algorithms and low-text detection.
   - MMR ranking logic.
2. **Integration Tests (`tests/integration/`):**
   - FastAPI HTTP endpoints with `httpx.AsyncClient`.
   - PostgreSQL repository tests with rollback transactions.
   - Refresh-token reuse detection scenarios.
   - Mocked external services (Gemini, S3, Qdrant, Neo4j) to test orchestration resilience.
3. **Security & Isolation Tests:**
   - Tenant isolation tests: verifying User B cannot read, mutate, or delete User A's documents, quiz attempts, graph nodes, or vector chunks.
   - Expired token, revoked token, and malicious payload tests.
4. **Coverage Targets:**
   - Domain & services coverage $\ge 85\%$.

---

## 7. Approval Request & Next Steps

This technical audit confirms that the repository is completely clean of broken legacy backend code, possesses approved architectural designs, and is ready for Phase 1 implementation.

**Immediate Next Step Upon Approval:**
Proceed with **Phase 1: Production Authentication, Database, and Security** (Prompt 2):
1. Create `backend/` project structure and configure `pyproject.toml`.
2. Configure async PostgreSQL connection and Alembic.
3. Create the initial database models and `001_initial` migration matching `docs/data/001_initial_schema.sql`.
4. Implement full authentication (Argon2id, JWT, rotating refresh with reuse detection, Google OAuth, password reset, rate limiting).
5. Add automated tests for all authentication and database capabilities.

*Awaiting user approval before writing application code or creating migrations.*
