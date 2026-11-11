# Code style
- Python: ruff (line 100), full type hints, mypy-clean; async everywhere in I/O; `from __future__` not needed (3.13). Small functions, domain language in names, no empty abstractions.
- Domain: dataclasses/value objects, invariants enforced in constructors/methods; raise `DomainError` subclasses.
- TypeScript: strict, oxlint + oxfmt, no `any`, functional React components, server state via generated client.
- Dart: `dart format`, `flutter analyze` clean.
- Comments explain why, not what. Delete dead code; no compat shims.
- Commits/PRs small and focused; tests accompany behavior changes.
