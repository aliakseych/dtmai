---
name: migrations
description: Use when changing database tables or writing Alembic revisions.
---

# Migrations
- One Postgres schema and one Alembic branch per module. First revision: `branch_labels=("<m>",)`, `down_revision=None`, `CREATE SCHEMA IF NOT EXISTS <m>`.
- Add the schema to `SCHEMAS` in `apps/api/migrations/env.py`.
- Autogenerate scoped: `uv run alembic -x schema=<m> revision --autogenerate --head <m>@head -m "msg"`; review by hand.
- Apply: `uv run python -m app migrate` (= `alembic upgrade heads`). Version table in `public`.
- Never edit applied revisions. Make destructive changes in two steps (expand, then contract).
