# Neo4j knowledge model

Aura / Community: **one database**. Isolation is `user_id` on every node and
relationship plus uniqueness constraints plus repository query guards.

Numeric mastery is **not** stored on the graph. `STRUGGLES_WITH` is a boolean
summary written after PostgreSQL commits a `beginner` band with \(n \ge 3\).

## Labels and properties

| Label | Required properties | Notes |
| --- | --- | --- |
| `User` | `user_id` | Mirrors Postgres users.id |
| `Document` | `user_id`, `document_id`, `filename` | |
| `Chapter` | `user_id`, `chapter_id`, `title`, `ordinal` | |
| `Chunk` | `user_id`, `chunk_id`, `page_start`, `page_end` | Text lives in Postgres/Qdrant |
| `Concept` | `user_id`, `concept_id`, `name`, `normalized_name` | |
| `Question` | `user_id`, `question_id`, `difficulty` | Stem lives in Postgres |

## Relationship types

Direction convention: `(from)-[:TYPE]->(to)`.

| Type | From → To | Properties | Adaptive? |
| --- | --- | --- | --- |
| `OWNS` | User → Document / Concept / Question | | no |
| `CONTAINS` | Document → Chapter → Chunk | | no |
| `PART_OF` | Concept → Document or Chapter | `confidence`, `chunk_ids`, `prompt_version`, `status` | no |
| `RELATED_TO` | Concept → Concept | same provenance | no |
| `USES` | Concept → Concept | provenance | no |
| `PREREQUISITE_OF` | Concept A → Concept B (A must precede B) | provenance + `confidence` + `status` | **yes if** `status='confirmed'` **or** (`status='pending'` and `confidence >= 0.75`) **and** user has not `rejected` |
| `TEACHES` | Chunk → Concept | provenance | no |
| `REFERENCES` | Concept → Chunk | provenance | no |
| `TESTS` | Question → Concept | `is_primary` | no |
| `STRUGGLES_WITH` | User → Concept | `since`, `evidence_n` | derived |

`status` on extracted edges: `pending` \| `confirmed` \| `rejected`.
User confirm/reject is stored on the relationship; rejected edges never drive
path planning.

Provenance blob on every LLM edge:

```
confidence: float  # 0-1
chunk_ids: string[]  # Postgres chunk UUIDs
prompt_version: string
extracted_at: datetime
source: 'llm' | 'user'
```

## Constraints and indexes

See `docs/data/neo4j_constraints.cypher`.

## Cycle policy

Before writing `PREREQUISITE_OF` from `a` to `b`, run a path check `b` ⇢ `a`.
If a path exists, **do not merge**; log `skipped_cycle` on the ingestion job
and keep the edge out of adaptive queries. Bidirectional proposals collapse to
the higher-confidence direction; equal confidence → neither (user must confirm).

## Key queries

See `docs/data/neo4j_queries.cypher`. All queries take `$user_id` first and
filter **every** node and relationship hop.
