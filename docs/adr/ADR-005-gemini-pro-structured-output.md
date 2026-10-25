# ADR-005: Gemini 2.5 Pro via AI Studio, schema-validated

## Status

Accepted (product choice)

## Context

You selected Google AI Studio + Gemini 2.5 Pro for all generation. Extraction
volume will dominate cost.

## Decision

One model id `GEMINI_MODEL` (default `gemini-2.5-pro`, **verify at S3**).
All outputs parsed by Pydantic; one repair retry; timeouts; `llm_call_logs`.
Prompts are versioned files.

## Consequences

Higher groundedness chance vs Flash; higher bill. Cost routing to Flash for
extract is a future ask, not a silent swap.
