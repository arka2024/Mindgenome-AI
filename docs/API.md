# HTTP API

Base path: `/api/v1`. OpenAPI source: `docs/openapi/openapi.yaml`.
Frontend generates a typed client from that file in Sprint 1.

## Conventions

| Topic | Rule |
| --- | --- |
| Auth | `Authorization: Bearer <access>` except register/login/refresh/oauth |
| Refresh | `POST /auth/refresh` with body `{refresh_token}`; rotation + reuse detection |
| Pagination | `page` (1-based) + `page_size` (default 20, max 100). Envelope `{items, page, page_size, total}` |
| Errors | RFC 7807 `application/problem+json` |
| Idempotency | Header `Idempotency-Key` required on `POST /documents`, `POST /quiz-attempts`, `POST /quiz-attempts/{id}/submit` |
| Versioning | URL version. Breaking change → `/api/v2`. Additive fields are non-breaking |
| Correlation | Echo `X-Request-Id` (generate if missing) |

### Problem details

```json
{
  "type": "https://mindgenome.ai/problems/validation",
  "title": "Validation error",
  "status": 422,
  "detail": "choices must contain exactly one correct index",
  "instance": "/api/v1/quiz-attempts",
  "request_id": "01J..."
}
```

Registered `type` URIs: `validation`, `unauthorized`, `forbidden`, `not-found`,
`conflict`, `rate-limited`, `upload-rejected`, `ingestion-failed`,
`low-retrieval-confidence`, `dependency-unavailable`.

## Endpoint table

| Method | Path | Auth | Idempotent | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | no | yes (email) | Create user + role `user` |
| POST | `/auth/login` | no | no | Password grant → access+refresh |
| POST | `/auth/refresh` | refresh | no | Rotate refresh |
| POST | `/auth/logout` | yes | no | Revoke refresh family |
| GET | `/auth/google/start` | no | no | Redirect to Google |
| GET | `/auth/google/callback` | no | no | Code exchange, upsert user |
| GET | `/auth/me` | yes | — | Current user |
| POST | `/documents` | yes | **key** | Upload PDF/DOCX, enqueue job |
| GET | `/documents` | yes | — | List mine |
| GET | `/documents/{id}` | yes | — | Metadata + warnings |
| GET | `/ingestion-jobs/{id}` | yes | — | Status machine + progress |
| GET | `/graph` | yes | — | Dashboard subgraph |
| POST | `/graph/edges/{id}/review` | yes | yes | confirm/reject edge |
| POST | `/tutor/ask` | yes | no | Grounded Q&A |
| POST | `/learning-sessions` | yes | **key** | Start learn/remedial/revision |
| GET | `/learning-sessions/{id}` | yes | — | Current section + rationale |
| POST | `/quiz-attempts` | yes | **key** | Create checkpoint quiz |
| POST | `/quiz-attempts/{id}/submit` | yes | **key** | Score + mastery recompute |
| GET | `/mastery` | yes | — | Concept scores + traces |
| GET | `/mastery/{concept_id}` | yes | — | Trace + history |
| GET | `/learning-path` | yes | — | Ordered recommendations + because |
| GET | `/dashboard` | yes | — | Genome summary, weak areas, jobs |
| GET | `/health` | no | — | Liveness |
| GET | `/ready` | no | — | Postgres/Redis ping; Neo4j/Qdrant/Gemini as degraded flags |

## Status mapping

| HTTP | When |
| --- | --- |
| 202 | Upload accepted, job queued |
| 409 | Idempotency key reused with different body; duplicate email; cycle reject |
| 413 | File too large |
| 415 | Bad type / magic mismatch |
| 422 | Pydantic / domain validation |
| 429 | Rate limit |
| 503 | Required dependency down (writes that need it) |
