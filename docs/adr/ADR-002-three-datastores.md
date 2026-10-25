# ADR-002: Postgres + Neo4j + Qdrant, no duplicated SoT

## Status

Accepted

## Context

Relational learner state, recursive prerequisites, and semantic retrieval have
different access patterns.

## Decision

- PostgreSQL: users, documents, chunks text, attempts, **numeric mastery**.
- Neo4j: concept topology, provenance on edges, `STRUGGLES_WITH` flag only.
- Qdrant: MiniLM vectors and citation payload ids.

Cytoscape never writes.

## Consequences

Ingestion is an eventual-consistent saga. Job status is the user-visible lock.
We will not store mastery floats on Neo4j “for convenience”.
