# MindGenome AI — Backend Service

Production-ready backend for MindGenome AI personal knowledge graph and adaptive learning platform.

## Technology Stack

- **Framework:** Python 3.12+, FastAPI, Pydantic v2
- **Database:** PostgreSQL 16 (SoT), SQLAlchemy 2.0 Async, Alembic
- **Caching & Broker:** Redis
- **Background Jobs:** Celery
- **Security:** Argon2id, JWT (15m), Rotating Refresh Tokens (SHA-256 hashed, reuse detection), Google OAuth (PKCE)
- **Vector & Graph:** Qdrant Cloud / Local, Neo4j Aura / Local
- **AI:** Google Gemini 2.5 Pro (Google AI Studio)

## Local Development Setup

### 1. Requirements

- Python 3.11+ or 3.12+
- PostgreSQL 16 (or Docker)
- Redis 7+ (or Docker)

### 2. Environment Configuration

Copy `.env.example` from project root to `backend/.env`:

```bash
cp ../.env.example .env
```

Ensure the database URL matches your local PostgreSQL instance:
```env
DATABASE_URL=postgresql+asyncpg://mindgenome:mindgenome@localhost:5432/mindgenome
DATABASE_URL_SYNC=postgresql://mindgenome:mindgenome@localhost:5432/mindgenome
```

### 3. Install Dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Database Migrations

Apply database migrations:

```bash
alembic upgrade head
```

### 5. Running the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation:
- Swagger UI: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- ReDoc: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### 6. Running Tests

```bash
pytest -v
```

To run with coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

## Render Deployment

Configure the Render web service to use Python 3.12 and
`Mindgenome-AI-main/backend` as its repository root directory. The
`.python-version` file pins Python 3.12.10 so Render does not select a newer
Python release unexpectedly. If deploying with Docker, the Dockerfile binds
Uvicorn to Render's `PORT` and serves the liveness check at `/health`. Set
Render's health check path to `/health`; use `/ready` separately to verify
database and service dependencies.

The Render Blueprint in `infra/render.yaml` configures only the static
frontend. Configure the backend web service separately in the Render dashboard.
Set `APP_ENV=production` and set `DATABASE_URL` to the intended persistent
Render PostgreSQL database. The application also recognizes Render's
`RENDER=true`/`RENDER_SERVICE_ID` environment values and refuses to start
against SQLite there. Standard `postgresql://` Render URLs are normalized to
the asyncpg driver automatically. Do not copy credentials into source files,
logs, or support messages.

Set
`CORS_ORIGINS` to a JSON list containing the deployed frontend origin, for
example `["https://mindgenomeai.vercel.app"]`, and set `FRONTEND_PUBLIC_URL`
to `https://mindgenomeai.vercel.app`. Keep credentials in Render environment
variables, not in this repository.

### Production database migrations

The application never applies schema changes at startup. Local SQLite may use
`create_all()` for development only; on Render, startup verifies PostgreSQL,
the Alembic head, and the chunk embedding columns before serving requests.
Ingestion workers perform the same verification before processing their first
job. Configure the API and each worker with the same `DATABASE_URL`.

#### Temporary startup database diagnostic

The backend temporarily emits a `temporary_database_diagnostic` structured log
before enforcing the production PostgreSQL requirement. It reports only the
database driver, whether `DATABASE_URL` was explicitly configured, and (for
SQLite) the resolved file path, file existence, table names, row counts, and
Alembic revision. It never logs the URL or row contents and opens SQLite files
in read-only mode. Render disk persistence is reported as unknown because the
backend configuration in this repository does not declare the managed service's
disk mount.

After deploying this temporary diagnostic, open the backend service's Render
**Logs**, select the latest deploy/startup, and search for
`temporary_database_diagnostic`. The production PostgreSQL validation remains
enabled, so this diagnostic does not make an SQLite deployment start
successfully. Once the production database has been identified, remove the
temporary module `app/db/diagnostics.py`, its import and invocation in
`app/db/session.py`, the diagnostic tests, and this section of the README.

From the backend service root in Render Shell, first inspect the migration
state:

```bash
alembic -c alembic.ini heads
alembic -c alembic.ini current
```

If the database is already at `001_initial`, apply the non-destructive
embedding-column migration with:

```bash
alembic -c alembic.ini upgrade head
```

The expected new revision is `002_embedding_provenance`; it only adds three
nullable columns to `chunks` and does not drop or recreate data. Confirm with:

```bash
alembic -c alembic.ini current
```

If `alembic current` reports no revision while application tables already
exist, **do not run `upgrade head` or `stamp` blindly**. The first migration is
a baseline that creates the schema. Back up the database, compare its existing
schema with revision `001_initial`, then only if they match exactly, mark that
baseline and apply the additive migration:

```bash
alembic -c alembic.ini stamp 001_initial
alembic -c alembic.ini upgrade head
```

`stamp` changes only Alembic's revision record; it does not alter the schema.
Never use it to bypass a schema mismatch. If Render is currently running on
SQLite and the intended persistent PostgreSQL database has not been configured,
identify and back up the current data first. Pointing `DATABASE_URL` at
PostgreSQL does not transfer SQLite users, documents, chunks, or jobs.

Ingestion logs include elapsed time for parsing, embedding, vector storage,
concept extraction, and graph building. Scanned PDFs OCR up to three pages
concurrently; check these stage timings in Render logs when investigating a
slow document.

Document jobs run in the API process by default so they do not get stuck in
Redis without a Celery worker. Set `CELERY_ENABLED=true` only when a Celery
worker consuming the configured broker is deployed and running. The Docker
Compose backend enables Celery because its worker service is included.

## Embedding model and safe migration

Document chunk vectors are stored in **Qdrant**. MongoDB is not the vector
database. Ingestion embeds chunks, while `/api/v1/tutor/ask` embeds learner
questions and retrieves matching chunks. The configured provider is Google
Gemini's `gemini-embedding-001`, with normalized 768-dimensional vectors.
Query and document requests use the API's `RETRIEVAL_QUERY` and
`RETRIEVAL_DOCUMENT` task types, respectively. Texts are sent in bounded batches
using the existing `GEMINI_API_KEY`; no local embedding model or separate
inference service is required. API failures, including quota exhaustion, stop
the operation rather than silently switching models.

Google AI Studio's free-tier availability and quotas can change and are subject
to Google's terms. Uploaded document text and learner queries are sent to
Google's API for embedding; review Google's current data-use terms and your
privacy requirements before enabling this in production. Do not send sensitive
or regulated documents unless the configured service terms permit that use.

Every model/version uses a separate Qdrant collection by default:
`<QDRANT_COLLECTION>_<EMBEDDING_VERSION>`. Existing MiniLM and Qwen collections
are left untouched. Search filters by model, version and dimension, and chunks
record embedding provenance in PostgreSQL. Reprocessing preserves chunk IDs;
stale points in the active collection are removed only after new embeddings
pass dimension/normalization checks and have been upserted successfully.

### Production rollout

1. Back up PostgreSQL and Qdrant. Do not delete the existing MiniLM collection
   during this rollout.
2. Deploy the application dependencies and run the database migration:

   ```bash
   cd backend
   alembic upgrade head
   ```

3. Configure the Render backend and **every Celery worker** with the same
   embedding settings. Keep `GEMINI_API_KEY` secret in Render:

   ```env
   EMBEDDING_MODEL=gemini-embedding-001
   EMBEDDING_VERSION=gemini_embedding_001_v1
   EMBEDDING_DIMENSION=768
   EMBEDDING_BATCH_SIZE=32
   QDRANT_COLLECTION=mindgenome_chunks
   EMBEDDING_COLLECTION_NAME=
   GEMINI_API_KEY=<your Google AI Studio API key>
   ```

   Leave `EMBEDDING_COLLECTION_NAME` empty to create/use the versioned Gemini
   collection. Do not enable `CELERY_ENABLED` until a worker is deployed.
4. Deploy the API, verify `/ready`, and ensure the new Qdrant collection is
   created at the configured dimension. Test a new document and tutor question
   before re-indexing existing content. Run
   `python -m scripts.smoke_test_embeddings` from the backend service root to
   check the Gemini API call, Qdrant insertion, metadata filtering and
   retrieval.
5. Start with a dry run, then re-index gradually:

   ```bash
   cd backend
   python -m scripts.reindex_embeddings --dry-run
   python -m scripts.reindex_embeddings --limit 5
   python -m scripts.reindex_embeddings
   ```

   The command uses the running Celery worker when `CELERY_ENABLED=true`;
   otherwise it processes documents sequentially in the command process. It
   selects documents whose chunk provenance does not match the configured
   model/version/dimension. Monitor failed jobs and Qdrant points before
   continuing. Old MiniLM and Qwen vectors remain in their original
   collections.
6. To roll back, redeploy the previous application version that supports
   MiniLM and point it to the **actual existing MiniLM collection name**. The
   current embedding service intentionally accepts only Gemini embeddings; do
   not change model settings to MiniLM in this version. Do not delete either
   collection until the rollback is validated.

### Retrieval evaluation

No representative lecture-document benchmark dataset was available, so no
MiniLM-vs-Gemini quality or latency comparison is claimed. To measure it,
prepare a UTF-8 JSONL dataset with one record per question, the candidate
passages, and the indices of the relevant passages:

```json
{"query":"How does gradient descent update model parameters?","candidates":["Passage A","Passage B"],"relevant_indices":[1]}
```

On a development/evaluation machine, install the evaluation dependencies with
`pip install -e ".[dev]"`, then run:

```bash
python -m scripts.benchmark_embeddings --dataset path\to\lecture_queries.jsonl --top-k 5
```

The script reports Recall@K, MRR and elapsed time for both models on the same
examples. Gemini calls count against the configured API quota. Use held-out
questions and passages from your own lecture materials; adjust
`RAG_MIN_SIMILARITY_SCORE` only after reviewing retrieval results and grounded
answer quality. Re-indexed documents retain their source text, document/chunk
IDs, page range and chapter/section metadata in Qdrant payloads.
