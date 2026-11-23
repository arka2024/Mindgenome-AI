# ADR-009: Render + Aura + Qdrant Cloud + S3-compatible uploads

## Status

Accepted

## Context

You chose Render over AWS Terraform for v1.

## Decision

`infra/render.yaml` for API, worker, static, Postgres, Redis.
Neo4j Aura and Qdrant Cloud are external (Render does not host them well).
Originals go to S3-compatible storage, not the container filesystem.

## Consequences

Fewer YAML files than Terraform; vendor lock-in to Render primitives.
AWS remains on the not-now list.
