# ADR-006: all-MiniLM-L6-v2, 384 dimensions, cosine

## Status

Accepted

## Context

You selected MiniLM for v1 speed/cost.

## Decision

Pin `sentence-transformers==` in S3, Qdrant vector size 384, cosine.
Re-embedding is a full collection rebuild if we ever change models.

## Consequences

Good enough for notes-scale corpora. Evaluation harness in S3 decides if we
must ask to move to mpnet (768-d).
