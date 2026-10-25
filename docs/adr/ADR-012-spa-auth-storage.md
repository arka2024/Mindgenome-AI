# ADR-012: SPA token storage

Status: accepted (v1 demo)

## Decision

Access JWT lives **only in memory** (Zustand). Refresh JWT lives in
**sessionStorage** (tab-scoped) so a reload can rotate without localStorage
persistence. Production API should set an **httpOnly Secure cookie** for refresh
and this client will drop sessionStorage.

## Why not localStorage

XSS can exfiltrate it for the lifetime of the token. sessionStorage dies with
the tab; memory access dies on refresh (then we rotate).

## Cookie fallback

When `VITE_AUTH_COOKIE=true` and the API shares a parent domain, skip storing
refresh on the client; `credentials: 'include'` only.
