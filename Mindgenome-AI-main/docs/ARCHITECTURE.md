# System architecture

Modular monolith. One API process, one worker process, three datastores.
Cytoscape is visualization only.

## C4 — context

```mermaid
C4Context
    title MindGenome AI — system context
    Person(learner, "Learner", "Uploads notes, studies, takes quizzes")
    System(mg, "MindGenome AI", "Document NLP, knowledge graph, grounded tutor, mastery, adaptive path")
    System_Ext(gemini, "Google Gemini 2.5 Pro", "Structured extraction, tutor, quiz gen")
    System_Ext(googleId, "Google Identity", "OAuth 2.0")
    System_Ext(s3, "S3-compatible object storage", "Original PDF/DOCX")
    Rel(learner, mg, "HTTPS / React SPA")
    Rel(mg, gemini, "GenerateContent, JSON schema")
    Rel(mg, googleId, "OAuth code flow")
    Rel(mg, s3, "Put/Get objects")
```

## C4 — containers

```mermaid
C4Container
    title MindGenome AI — containers
    Person(learner, "Learner")
    Container(web, "frontend", "React + TS + Tailwind + Cytoscape", "Auth, genome, learn, tutor, quiz")
    Container(api, "api", "FastAPI / uvicorn", "/api/v1, JWT, enqueue jobs")
    Container(worker, "worker", "Celery", "Parse, embed, extract, graph write")
    ContainerDb(pg, "PostgreSQL", "Render Postgres", "Users, docs, attempts, mastery")
    ContainerDb(neo, "Neo4j", "Aura", "Concepts and relationships")
    ContainerDb(qd, "Qdrant", "Qdrant Cloud", "Chunk vectors")
    ContainerDb(redis, "Redis", "Render Redis", "Broker, rate limit, cache")
    Container_Ext(gemini, "Gemini")
    Container_Ext(s3, "Object storage")
    Rel(learner, web, "HTTPS")
    Rel(web, api, "REST JSON, Bearer")
    Rel(api, pg, "SQL")
    Rel(api, neo, "Cypher reads")
    Rel(api, qd, "Query points")
    Rel(api, redis, "Rate limit, enqueue")
    Rel(api, worker, "Celery tasks via Redis")
    Rel(worker, pg, "SQL")
    Rel(worker, neo, "Cypher writes")
    Rel(worker, qd, "Upsert")
    Rel(worker, gemini, "Extract / generate")
    Rel(worker, s3, "Read originals")
    Rel(api, s3, "Presign upload")
```

## Sequence — document ingestion

```mermaid
sequenceDiagram
    actor U as Learner
    participant API as api
    participant S3 as object store
    participant PG as PostgreSQL
    participant Q as Redis/Celery
    participant W as worker
    participant QD as Qdrant
    participant G as Gemini
    participant N as Neo4j

    U->>API: POST /api/v1/documents (Idempotency-Key)
    API->>API: magic bytes, size, MIME
    API->>S3: PutObject
    API->>PG: insert documents + ingestion_jobs queued
    API->>Q: ingest_document.delay(job_id)
    API-->>U: 202 {document_id, job_id, status}

    W->>PG: status=parsing
    W->>S3: GetObject
    W->>W: PyMuPDF / python-docx, header strip
    alt low text
        W->>PG: failed, error_code=low_text
    else ok
        W->>PG: status=chunking, insert chapters/chunks
        W->>PG: status=embedding
        W->>QD: upsert points filterable by user_id
        W->>PG: status=extracting
        W->>G: structured concepts/edges (prompt file version)
        W->>PG: upsert concepts, llm_call_logs
        W->>PG: status=graph_built
        W->>N: MERGE nodes/edges + cycle guard
        W->>PG: status=ready, documents.status=ready
    end
    U->>API: GET /api/v1/ingestion-jobs/{id}
    API->>PG: read
    API-->>U: progress_pct + status
```

## Sequence — hybrid (graph-augmented) RAG

```mermaid
sequenceDiagram
    actor U as Learner
    participant API as api
    participant QD as Qdrant
    participant PG as PostgreSQL
    participant N as Neo4j
    participant G as Gemini

    U->>API: POST /api/v1/tutor/ask
    API->>API: embed question (MiniLM)
    API->>QD: query must user_id, top_k=12
    API->>PG: load chunk bodies + citation metadata
    API->>N: optional TEACHES/REFERENCES expansion
    API->>API: MMR fusion, confidence band
    alt confidence low
        API-->>U: 200 grounded=false, message=insufficient sources
    else medium or high
        API->>G: tutor prompt + delimited untrusted document text + JSON schema
        G-->>API: AnswerDTO citations required
        API->>PG: llm_call_logs
        API-->>U: 200 answer + citations
    end
```

## Sequence — quiz → mastery → dependencies → remedial

```mermaid
sequenceDiagram
    actor U as Learner
    participant API as api
    participant D as domain.mastery
    participant PG as PostgreSQL
    participant N as Neo4j
    participant P as domain.path

    U->>API: POST /api/v1/quiz-attempts/{id}/submit
    API->>PG: persist attempt_answers (idempotent)
    API->>D: compute_mastery(answers, revisions)
    D-->>API: components + M + band
    API->>PG: upsert mastery_scores, append mastery_history
    alt band beginner and n>=3
        API->>N: MERGE STRUGGLES_WITH
    else
        API->>N: DELETE STRUGGLES_WITH if present
    end
    API->>N: weakest ancestor via PREREQUISITE_OF
    API->>P: next_step(mastery_map, graph)
    alt remedial
        API-->>U: 200 next.mode=remedial, because=weak prerequisite
    else continue
        API-->>U: 200 next.mode=learn, because=prereqs ready
    end
```

## Package layout (backend)

Domain **must not** import FastAPI, Celery, SQLAlchemy, Neo4j, Qdrant, LangChain, or Google SDKs.

```
backend/
  pyproject.toml
  alembic.ini
  alembic/versions/
  app/
    main.py
    api/                # routers, deps, error handlers
      v1/
        auth.py
        documents.py
        graph.py
        tutor.py
        learning.py
        quizzes.py
        mastery.py
        dashboard.py
    schemas/            # Pydantic API models
    services/           # use cases (orchestration)
    domain/             # pure: mastery, path, validation
      mastery.py
      path.py
      evidence.py
    repositories/       # ports
    adapters/           # postgres, neo4j, qdrant, gemini, s3, redis
    workers/            # celery app + tasks
    core/               # settings, logging, security
    prompts/            # versioned .md + .schema.json (not inline)
  tests/
    unit/
    integration/
    golden/
```

Frontend layout is in `docs/FRONTEND.md`.

## SoT rules

| Data | Write | Read path |
| --- | --- | --- |
| Mastery numbers, attempts | Postgres | API → domain → Postgres |
| STRUGGLES_WITH | Neo4j after Postgres commit | Dashboard graph |
| Chunk text | Postgres | RAG loads bodies after Qdrant ids |
| Vectors | Qdrant | Tutor retrieve |
| Prerequisite topology | Neo4j | Path planner |
| Cytoscape elements | never persisted | Built from graph API |

## Alembic plan

1. Sprint 1: `001_initial` = `docs/data/001_initial_schema.sql` (enums, tables, RLS, indexes).
2. Later sprints: additive migrations only; no rewrite of 001.
3. Expand/contract for enum changes.
4. CI: `alembic upgrade head` against the Postgres service container before tests.
5. Render deploy: release command `alembic upgrade head` gated on health of Postgres.

## Risks (owned)

| Risk | Mitigation |
| --- | --- |
| Gemini Pro cost on every extract | Log tokens; later ask to route extract→Flash (not swapping stack) |
| Noisy edges | confidence + provenance + user confirm + 0.75 adaptive floor + cycle guard |
| Three-store drift | job state machine, idempotent upserts, retry from last stage |
| Neo4j Community tenancy | property scope + constraints + query guards + tests that a second user_id returns empty |
| Messy PDFs | low-text fail-closed, golden files in S2 |
| Prompt injection via PDF | delimited untrusted text, citations required, Pydantic answer schema |
