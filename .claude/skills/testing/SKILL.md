---
name: testing
description: Use when writing or running backend tests.
---

# Testing
- `cd apps/api && uv run pytest`. Layout: `tests/<module>/unit` (pure domain/application with fakes, no I/O) and `tests/<module>/integration` (real Postgres via dev compose).
- TDD: write the failing unit test first for invariants, signature checks, scoring, ELO.
- HTTP mocks via `respx`; async tests use pytest-asyncio (auto mode).
- Also run `ruff check`, `mypy app`. Verify the changed behavior, not just that it builds.
