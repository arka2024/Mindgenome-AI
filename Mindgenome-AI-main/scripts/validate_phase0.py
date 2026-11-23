"""Validate Phase 0 architecture artifacts. Stdlib only. Python 3.12+."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TABLES = (
    "users",
    "documents",
    "chapters",
    "chunks",
    "concepts",
    "questions",
    "question_concepts",
    "quiz_attempts",
    "attempt_answers",
    "mastery_scores",
    "mastery_history",
    "learning_sessions",
    "revision_schedule",
    "ingestion_jobs",
    "llm_call_logs",
)

REQUIRED_INGESTION_STATES = (
    "queued",
    "parsing",
    "chunking",
    "embedding",
    "extracting",
    "graph_built",
    "ready",
    "failed",
)

REQUIRED_ADRS = (
    "ADR-001-modular-monolith.md",
    "ADR-002-three-datastores.md",
    "ADR-003-rule-based-mastery.md",
    "ADR-004-graph-augmented-retrieval.md",
    "ADR-005-gemini-pro-structured-output.md",
    "ADR-006-minilm-384.md",
    "ADR-007-auth-password-and-google.md",
    "ADR-008-property-scoped-tenancy.md",
    "ADR-009-render-managed-data.md",
    "ADR-010-trunk-based.md",
    "ADR-011-not-now.md",
)

REQUIRED_OPENAPI_PATHS = (
    "/auth/register",
    "/auth/login",
    "/auth/refresh",
    "/auth/google/start",
    "/documents",
    "/ingestion-jobs/{job_id}",
    "/graph",
    "/tutor/ask",
    "/learning-sessions",
    "/quiz-attempts",
    "/mastery",
    "/learning-path",
    "/dashboard",
)


class CheckError(Exception):
    """A single failed Phase 0 invariant."""


def _read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise CheckError(f"missing file: {relative}")
    return path.read_text(encoding="utf-8")


def check_sql() -> None:
    sql = _read("docs/data/001_initial_schema.sql")
    for table in REQUIRED_TABLES:
        if not re.search(rf"CREATE TABLE {table}\b", sql):
            raise CheckError(f"SQL missing table {table}")
    for state in REQUIRED_INGESTION_STATES:
        if f"'{state}'" not in sql:
            raise CheckError(f"SQL missing ingestion status {state}")
    if "ENABLE ROW LEVEL SECURITY" not in sql:
        raise CheckError("SQL missing RLS")
    if "user_id" not in sql:
        raise CheckError("SQL missing user_id tenancy")


def check_graph() -> None:
    queries = _read("docs/data/neo4j_queries.cypher")
    if queries.count("$user_id") < 8:
        raise CheckError("Cypher queries must bind $user_id densely")
    constraints = _read("docs/data/neo4j_constraints.cypher")
    if "user_id" not in constraints:
        raise CheckError("Neo4j constraints missing user_id")


def check_openapi() -> None:
    spec = _read("docs/openapi/openapi.yaml")
    if "/api/v1" not in spec:
        raise CheckError("OpenAPI servers must use /api/v1")
    if "application/problem+json" not in spec:
        raise CheckError("OpenAPI must declare RFC 7807 problem+json")
    for path in REQUIRED_OPENAPI_PATHS:
        # YAML keys are indented path strings
        if path not in spec:
            raise CheckError(f"OpenAPI missing path {path}")


def check_adrs() -> None:
    for name in REQUIRED_ADRS:
        _read(f"docs/adr/{name}")


def check_env_example() -> None:
    text = _read(".env.example")
    for key in (
        "DATABASE_URL",
        "NEO4J_URI",
        "QDRANT_URL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "EMBEDDING_DIM",
        "GOOGLE_OAUTH_CLIENT_ID",
        "S3_BUCKET",
    ):
        if key not in text:
            raise CheckError(f".env.example missing {key}")
    if "EMBEDDING_DIM=384" not in text:
        raise CheckError("EMBEDDING_DIM must be 384")
    if "gemini-2.5-pro" not in text:
        raise CheckError("default GEMINI_MODEL must be gemini-2.5-pro")


def check_mastery_doc() -> None:
    text = _read("docs/MASTERY.md")
    if "0.40" not in text or "0.20" not in text:
        raise CheckError("mastery weights missing")
    if "n_min" not in text and "n ≥ 3" not in text and "n >= 3" not in text and "1–2" not in text:
        raise CheckError("minimum evidence rule missing")


def check_render() -> None:
    text = _read("infra/render.yaml")
    if "mindgenome-api" not in text or "mindgenome-worker" not in text:
        raise CheckError("render.yaml must define api and worker")


def main() -> int:
    checks = (
        check_sql,
        check_graph,
        check_openapi,
        check_adrs,
        check_env_example,
        check_mastery_doc,
        check_render,
    )
    errors: list[str] = []
    for check in checks:
        try:
            check()
        except CheckError as exc:
            errors.append(str(exc))
    if errors:
        for item in errors:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1
    print("Phase 0 artifacts OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
