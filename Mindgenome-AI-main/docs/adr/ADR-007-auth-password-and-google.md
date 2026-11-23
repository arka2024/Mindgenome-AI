# ADR-007: Email/password + Google OAuth, rotating refresh

## Status

Accepted

## Context

You want both password and Google.

## Decision

Argon2id passwords, Google authorization code with PKCE, JWT access 15m,
opaque rotating refresh, RBAC table with a single `user` role in v1.

## Consequences

Account-linking rules in `docs/SECURITY.md`. Extra OAuth env vars on Render.
