# =============================================================================
# MindGenome AI - Multi-Stage Production Dockerfile
# Python 3.12-slim | Non-root runtime | Minimal attack surface
# =============================================================================

# Stage 1: Build virtual environment and wheels
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# Stage 2: Minimal runtime image
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=10000 \
    WEB_CONCURRENCY=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /opt/venv /opt/venv

# Create unprivileged system user
RUN groupadd -g 10001 mindgenome && \
    useradd -u 10001 -g mindgenome -m -s /bin/bash appuser

# Copy application source and configuration
COPY --chown=appuser:mindgenome app/ ./app/
COPY --chown=appuser:mindgenome alembic/ ./alembic/
COPY --chown=appuser:mindgenome alembic.ini .

# Create directory for local uploads/storage with proper permissions
RUN mkdir -p /app/storage && chown -R appuser:mindgenome /app/storage

USER appuser

EXPOSE 10000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://127.0.0.1:${PORT:-10000}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-10000}\" --workers \"${WEB_CONCURRENCY:-1}\""]
