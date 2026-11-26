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
Python release without a compatible CPU PyTorch wheel. If deploying with
Docker, the Dockerfile binds Uvicorn to Render's `PORT` and serves the
liveness check at `/health`. Set Render's health check path to `/health`; use
`/ready` separately to verify database and service dependencies.

In the Render environment, set `DATABASE_URL` to the production PostgreSQL
connection string using the `postgresql+asyncpg://` scheme. Set
`CORS_ORIGINS` to a JSON list containing the deployed frontend origin, for
example `["https://mindgenomeai.vercel.app"]`, and set `FRONTEND_PUBLIC_URL`
to `https://mindgenomeai.vercel.app`. Keep credentials in Render environment
variables, not in this repository.

Ingestion logs include elapsed time for parsing, embedding, vector storage,
concept extraction, and graph building. Scanned PDFs OCR up to three pages
concurrently; check these stage timings in Render logs when investigating a
slow document.

Document jobs run in the API process by default so they do not get stuck in
Redis without a Celery worker. Set `CELERY_ENABLED=true` only when a Celery
worker consuming the configured broker is deployed and running. The Docker
Compose backend enables Celery because its worker service is included.
