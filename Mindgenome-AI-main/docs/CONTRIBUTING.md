# Contributing

Trunk-based: branch from `main`, conventional commits, PR with green CI.

Phase 0 is design-only. Do not add application runtime until Sprint 1 is
approved.

```bash
python scripts/validate_phase0.py
python -m pytest tests/test_phase0_artifacts.py -q
```

After S1: ruff, mypy, eslint, compose tests — see `docs/DELIVERY.md`.
