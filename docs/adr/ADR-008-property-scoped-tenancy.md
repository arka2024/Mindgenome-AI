# ADR-008: Personal multi-tenant via user_id (no Neo4j multi-DB)

## Status

Accepted

## Context

Neo4j Community/Aura typically one database. Sharing is out of v1.

## Decision

Every Postgres row (except global enums), every Neo4j node/rel, every Qdrant
payload includes `user_id`. Unique keys are composite with `user_id`.
Repositories require `user_id`. Postgres RLS as defense in depth.

## Consequences

No document sharing, no org table. Cross-tenant tests are mandatory from S1
(auth) and S4 (graph).
