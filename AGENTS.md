# AGENTS.md — DTM AI

## Layout
- `apps/api` — FastAPI, SQLAlchemy async, Alembic, taskiq, aiogram. Modules in `app/modules/<m>/{domain,ports,application,infrastructure,wiring.py}`; HTTP in `app/interfaces/http/v1/<m>.py`.
- `apps/web`, `apps/admin` — Next.js 16 static export (bun workspaces). `apps/mobile` — Flutter.
- `packages/ui` (tokens/atoms), `packages/api-client` (generated), `packages/i18n` (messages).
- `deploy/` — compose, nginx, `DEPLOY.md`. `.claude/skills/*` — task playbooks (read the matching one first).
- Content is managed in the admin panel (ingestion, labeling, generation); there is no in-repo source data.

## Commands
- API: `cd apps/api && uv sync`, `uv run pytest`, `uv run ruff check . && uv run ruff format .`, `uv run mypy app`, `uv run python -m app api|worker|scheduler|migrate|seed`.
- First admin: register by email, then `uv run python -m app promote <email> [role ...]` (default `admin`).
- Content: `uv run python -m app ingest <file|dir> --source <code> --subject <code> --language <uz|ru> [--key --year N --base NAME]` (language is required; it must match the file text). Only `verified` questions are served: approve via the admin labeling cockpit or bulk-approve. A lesson appears in a path only once its verified pool reaches `max(min_pool, question_count)`.
- Lyceum stats: admin triggers a per-year import; edu.uz rate-limits (429), so the client backs off and `lyceums_import_concurrency` defaults to 2.
- Contract: `bun run gen:api` (exports `apps/api/openapi/openapi.json`, regenerates `packages/api-client`).
- Web: `bun install`, `bun run dev|build|lint`.
- Dev infra: `docker compose -f deploy/docker-compose.dev.yaml up -d`.

## Rules
- DDD, dependencies point inward: `domain` (pure Python, no framework/ORM) <- `ports` (Protocols) <- `application` (use cases) <- `infrastructure` (SQLAlchemy, SMTP, HTTP clients) and `interfaces` (routes, bot, jobs). Cross-module access only via another module's `ports`/`application`, never its ORM.
- OpenAPI owner is `apps/api`. Change an endpoint -> `bun run gen:api` -> commit `openapi.json` and the regenerated client. Never hand-write API types in frontends/mobile.
- One Postgres schema per module; one Alembic branch per module (see `migrations` skill).
- i18n: locales `uz-Latn` (default), `uz-Cyrl`, `ru`, `en`; keys must have parity in all four.
- Dynamic content: subjects, topics, question types, plans, lyceums come from the API/DB. Never hardcode them in code or UI.
- No secrets in the repo; config via env (`apps/api/app/settings.py`, `deploy/.env.sample`).
- Errors: raise `DomainError` subclasses; they render as `application/problem+json`.
- Payments: `PAYMENTS_ENABLED=false` hides all purchase UI; while off, `billing/wiring.py:FREE_WHILE_PAYMENTS_OFF` (personal mocks) is granted to everyone.
- Guests: `POST /v1/identity/guest` creates a `guest`-role user (no email/telegram); clients create one for any anonymous visitor and call `/v1/learning/merge-guest` after sign-in.
- Follow `CODESTYLE.md`; UI follows the `ui-ux` skill.

## Add a backend module
1. Create `apps/api/app/modules/<m>/` with `domain/ ports/ application/ infrastructure/ wiring.py`; ORM tables use `schema="<m>"` and `Base` from `app.shared.db`.
2. Add route file `app/interfaces/http/v1/<m>.py` and ONE line in `app/bootstrap/registry.py` (`MODULES`): `(<m>.router, "/<m>")`.
3. Add ONE entry to `SCHEMAS` in `apps/api/migrations/env.py`, append `%(here)s/migrations/versions/<m>` to `version_locations` in `apps/api/alembic.ini` (space-separated; `path_separator = space`), then `alembic revision` with `branch_labels=("<m>",)` creating the schema. Apply with `alembic upgrade heads`.
4. Add `tests/<m>/{unit,integration}`; run `bun run gen:api`.
