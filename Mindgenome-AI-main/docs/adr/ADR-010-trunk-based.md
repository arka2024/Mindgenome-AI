# ADR-010: Trunk-based development and OpenAPI SemVer

## Status

Accepted

## Context

Small team, one schema, one production.

## Decision

`main` is always releasable. PRs are short. GitFlow is rejected.
HTTP contract versions at `/api/v1` with SemVer in OpenAPI `info.version`.

## Consequences

Feature flags only if a PR cannot land dark. None needed in S1–S2.
