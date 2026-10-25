# Qdrant design

## Collection

| Setting | Value |
| --- | --- |
| Name | `mindgenome_chunks` (override with `QDRANT_COLLECTION`) |
| Vectors | one named vector `text`, size **384** |
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Distance | **Cosine** |
| Point id | `chunks.id` (UUID) |

Do not create per-user collections in v1 (operational explosion on Community/Cloud).
Isolation is a **mandatory** `must` filter on `user_id`.

## Payload schema

```json
{
  "user_id": "uuid",
  "document_id": "uuid",
  "chunk_id": "uuid",
  "chapter_id": "uuid|null",
  "chapter_title": "string|null",
  "heading_path": "string|null",
  "page_start": 1,
  "page_end": 1,
  "token_count": 412
}
```

Payload indexes (keyword / uuid as keyword, integers as integer):

- `user_id` (required for every query)
- `document_id`
- `chapter_id`

Never store the full chunk body in Qdrant; retrieve text from PostgreSQL
`chunks.body` after hits (Postgres remains document SoT). Store only ids and
citation fields in the payload.

## Chunking (Sprint 2)

1. Detect chapters/sections from headings and outline (PDF bookmarks, DOCX styles, numbered headings).
2. Strip repeating headers/footers/page numbers before chunking.
3. Target **512 tokens**, overlap **64 tokens**, split on paragraph/sentence boundaries; never cut a heading away from its first paragraph.
4. Each chunk carries `page_start`, `page_end`, `chapter_id`, `heading_path`.
5. Low-text / scanned PDFs: skip embedding, mark `documents.is_low_text`, surface a warning; job can still complete as `ready` with zero chunks if the user acknowledges, or `failed` with `error_code=low_text` — default **`failed` with warning payload** so we do not pretend a genome exists.

## Retrieval algorithm (Sprint 3)

v1 is **graph-augmented dense retrieval**, not lexical BM25. Adding a sparse
engine would violate the locked stack. If evaluation hit-rate is poor, we will
ask before introducing a lexical store.

Procedure `retrieve(user_id, query, filters?)`:

1. Embed query with MiniLM (same model, normalize for cosine).
2. Qdrant `query_points`:
   - vector = query
   - `limit = RETRIEVAL_TOP_K` (12)
   - filter **must** `user_id = $user_id` plus optional document/chapter
3. Drop hits with cosine similarity `< RETRIEVAL_MIN_SCORE` (0.35).
4. Load chunk rows from Postgres by id (still `user_id` scoped).
5. **Graph expansion (optional, tutor mode):** from concepts `TEACHES`/`REFERENCES` linked to hit chunks, pull up to 4 neighboring concept chunks that also pass the user filter. Cap total context chunks at 8.
6. **Context fusion:** greedy MMR (λ=0.7 relevance / 0.3 diversity on MiniLM cosine between chunks) so we do not paste three near-duplicate paragraphs.
7. **Confidence:**
   - `high` if top-1 score ≥ 0.55 and score gap (top1−top3) ≥ 0.08
   - `medium` if top-1 ≥ 0.35
   - `low` otherwise, or if zero hits after filtering

If confidence is `low`, the tutor **must not** invent an answer: return a
structured refusal with the best citations (if any) and ask the user to
narrow the question or upload more material.

Citation object required on every non-refusal answer:

`{ document_id, filename, chapter_title, page_start, page_end, chunk_id }`
