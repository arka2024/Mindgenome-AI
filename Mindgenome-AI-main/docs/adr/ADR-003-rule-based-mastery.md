# ADR-003: Transparent rule-based mastery (no trained model in v1)

## Status

Accepted

## Context

scikit-learn is allowed later as a baseline, not as the product identity.
Explainability is a design principle.

## Decision

Pure functions in `domain/mastery.py` with the 40/20/20/20 formula, 14-day
recency half-life, difficulty weights 0.7/1.0/1.3, exponential retention, and
`n >= 3` before weak labels. Full spec: `docs/MASTERY.md`.

## Consequences

Unit-testable with the Gradient Boosting worked example. We can add ML later
behind a flag without changing Postgres schema (new reason enum value).
