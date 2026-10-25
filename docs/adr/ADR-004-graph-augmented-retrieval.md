# ADR-004: Graph-augmented dense retrieval (not BM25)

## Status

Accepted

## Context

“Hybrid RAG” usually means dense + lexical. The locked stack has Qdrant and
Neo4j, not Elasticsearch/BM25/sparse vectors.

## Decision

v1 retrieval = MiniLM cosine in Qdrant **plus** optional Neo4j neighborhood
expansion and MMR fusion. Low cosine confidence refuses to answer.

## Consequences

We do not smuggle FAISS/Chroma/ES. If S3 evaluation hit-rate is poor, we ask
before adding a lexical component.
