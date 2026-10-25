# MindGenome AI

Personal knowledge graph and adaptive learning platform.

**Loop:** UPLOAD → NLP → CONCEPTS → GRAPH → LEARN → QUIZ → MASTERY → DEPENDENCIES → REMEDIAL / NEXT → UPDATED GENOME

This repository currently contains **Phase 0 architecture** (approved design artifacts). Application code starts in Sprint 1 after design sign-off.

## Locked v1 decisions

| Topic | Choice |
| --- | --- |
| Architecture | One modular monolith API + one Celery worker + three datastores |
| Frontend | React + TypeScript + Tailwind + Cytoscape.js |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Datastores | PostgreSQL (SoT), Neo4j (structure), Qdrant (vectors) |
| LLM | Gemini 2.5 Pro via Google AI Studio (verify model id at implementation) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, 384-d, cosine |
| Auth | Email/password (argon2id) + Google OAuth, JWT access + rotating refresh |
| Tenancy | Personal multi-tenant: `user_id` isolation, no sharing in v1 |
| Deploy | Render (`infra/render.yaml`) + Aura + Qdrant Cloud + S3-compatible uploads |
| Branching | Trunk-based (`main`), conventional commits, SemVer for the HTTP API |

## Docs map

| File | What it is |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | C4, sequences, package layout, SoT rules |
| [docs/MASTERY.md](docs/MASTERY.md) | Exact mastery formulas and evidence rules |
| [docs/GRAPH.md](docs/GRAPH.md) | Neo4j model + Cypher |
| [docs/QDRANT.md](docs/QDRANT.md) | Vectors, chunking, graph-augmented retrieval |
| [docs/API.md](docs/API.md) | REST contract summary |
| [docs/openapi/openapi.yaml](docs/openapi/openapi.yaml) | OpenAPI 3.1 source of the HTTP contract |
| [docs/SECURITY.md](docs/SECURITY.md) | Auth, uploads, prompt injection, OWASP map |
| [docs/FRONTEND.md](docs/FRONTEND.md) | Routes, state, a11y, design tokens |
| [docs/DELIVERY.md](docs/DELIVERY.md) | Environments, CI/CD, costing |
| [docs/adr/](docs/adr/) | Architecture Decision Records |
| [docs/data/001_initial_schema.sql](docs/data/001_initial_schema.sql) | PostgreSQL DDL (Alembic source in S1) |

## Phase 0 verification

Requires Python 3.12+ (no third-party packages):

```bash
python scripts/validate_phase0.py
```

Expected: `Phase 0 artifacts OK`.

## Git note (this workstation)

`git` was not on `PATH` when the project folder was created. Install Git for Windows, then:

```bash
cd %USERPROFILE%\mindgenome-ai
git init
git add .
git commit -m "docs: phase 0 architecture and data contracts"
```

## What is not in this commit

Sprint 1 implements FastAPI, React, Docker Compose, and auth. Do not treat empty package directories as the app; they are reserved in the tree documented in `docs/ARCHITECTURE.md`.
"# Mindgenome-AI" 
"# Mindgenome-AI" 
