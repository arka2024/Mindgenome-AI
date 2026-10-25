# ADR-001: Modular monolith (one API, one worker)

## Status

Accepted

## Context

We need document pipelines, RAG, graph writes, and interactive HTTP. Microservices
and Kubernetes are explicitly out of scope.

## Decision

Ship one FastAPI process and one Celery worker sharing a domain package.
Split only if a measured bottleneck appears after S8.

## Consequences

Simple local compose and Render services. We must keep domain pure so a later
split is possible. Risk: a slow extract holds the worker; mitigated with
Celery concurrency and job stages, not extra services.
