# ADR-014: Streaming Grounded RAG Chat & Source Drawer Linking

Status: accepted

## Context
Generic chatbots produce untrusted hallucinated answers. MindGenome AI positions itself as a grounded tutor where every claim must point back to exact source material (Document · Chapter · Page). When streaming responses via Server-Sent Events (SSE) or chunked HTTP, inline citation anchors `[cite:doc_id:chap_idx:page]` must be parsed progressively without causing layout jitter or broken markdown tokens.

## Decision
1. **Streaming Protocol**:
   - Backend streams SSE events: `event: token` for raw text, and `event: citation` for structured payload `{ id, documentId, documentTitle, chapterTitle, pageNumber, snippet, conceptId }`.
   - MSW mocks simulate this using progressive chunked delays (25ms per token interval) via `ReadableStream`.
2. **Citation Token Parsing**:
   - A lightweight streaming token parser extracts special semantic citation tokens `[doc_title § p.X]` and renders them as interactive Radix-accessible `<CitationChip />` components.
3. **Cross-System Bidirectional Linking**:
   - Clicking a `<CitationChip />` opens a sliding sheet (`SourcePreviewDrawer`) displaying the exact extracted snippet, page context, and document metadata.
   - Concurrently, if the citation contains a concept ID, it emits an active focus event to the Genome Knowledge Graph, centering the canvas or list item on that concept.

## Consequences
- High-trust user experience with zero hallucinations going unverified.
- Screen readers receive `aria-live="polite"` updates for stream completions and clear button names for citation anchors.
