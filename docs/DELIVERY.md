# Environments and delivery

## Environments

| Env | API | Data | Purpose |
| --- | --- | --- | --- |
| local | docker compose (S1) | Postgres, Redis, Neo4j, Qdrant, MinIO | Dev |
| CI | GitHub Actions service containers | ephemeral | PR gates |
| staging | Render (same blueprint as prod, smaller) | managed | Smoke after main |
| production | Render | Render Postgres/Redis, Aura, Qdrant Cloud, S3/R2 | Users |

## Branching: trunk-based

Single long-lived branch `main`. Short-lived PRs (< 2 days). No GitFlow.

Why: two-person team, continuous Alembic on one schema, GitFlow release
branches would duplicate Render envs we do not have. API compatibility uses
SemVer on OpenAPI (`0.y.z` until S8, then `1.0.0`).

Hotfix: PR to `main` like any other change.

## Commits and versions

- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- `feat!:` / `BREAKING CHANGE:` bumps OpenAPI major after 1.0.0.
- App version in `backend/pyproject.toml` and `frontend/package.json` kept in lockstep.

## CI (from S1, complete in S8)

On every PR to `main`:

- ruff, ruff format --check, mypy
- eslint, prettier --check, tsc --noEmit
- pytest unit + integration (compose services)
- vitest
- coverage gate (domain+services ≥ 80% once those packages exist)
- pip-audit, npm audit, Trivy, gitleaks
- docker build (layer cache)

Branch protection: required checks, no direct push to `main`, 1 review when a
second human exists (solo: yourself + green CI).

## CD (Render)

On merge to `main`:

1. Build and push images to GHCR.
2. Render autodeploy staging.
3. Release command: `alembic upgrade head`.
4. Smoke: `GET /health`, `GET /ready`.
5. **Manual approval** to promote the same image to production.

Rollback: Render instant rollback to previous deploy; if migration is
incompatible, restore Postgres PITR then rollback image (expand/contract
avoids this). Zero-downtime: Render rolling deploy of API; worker can run
one generation behind if tasks are version-tolerant.

## Infra as code

`infra/render.yaml` is the v1 blueprint. Terraform/AWS is **not now**.

Managed vs self-host (monthly, order-of-magnitude USD, 2026 ballpark — verify
at signup):

| Piece | v1 choice | Why | Rough USD |
| --- | --- | --- | --- |
| API + worker + static | Render | Matches your pick; ops time | 14–50 |
| Postgres | Render managed | PITR, less babysitting | 7–20 |
| Redis | Render | Celery + rate limit | 10 |
| Neo4j | Aura | Graph ops we should not self-host in v1 | 0–65 |
| Qdrant | Qdrant Cloud | Same | 0–25 |
| Uploads | R2 or S3 | Not Render disk | 1–5 |
| Gemini 2.5 Pro | AI Studio | You chose Pro for all gen; watch logs | highly variable |
| Self-host Neo4j+Qdrant on a VM | rejected for v1 | Backup/restore + upgrades eat the sprint | “cheaper” until it is not |

## Observability (progressive)

S1: structlog JSON + request id.
S3: `llm_call_logs`.
S8: Sentry, /metrics, Flower, uptime, backup restore test.

## Local git

This workstation did not have `git` on PATH when Phase 0 was written. Install
Git before Sprint 1 commits.
