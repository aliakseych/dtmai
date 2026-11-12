# DTM AI

Duolingo-style preparation for Uzbekistan DTM lyceum entrance exams: learner web app, admin, Flutter mobile, Telegram bot / Mini App, Click payments, AI explanations.

| Path | What |
|---|---|
| `apps/api` | FastAPI backend (Python 3.13, uv), source of the OpenAPI contract |
| `apps/web` | Next.js static export: landing + learner app + Mini App |
| `apps/admin` | Next.js static export admin |
| `apps/mobile` | Flutter app |
| `packages/*` | `ui`, `api-client`, `i18n` |
| `deploy/` | docker compose, nginx, runbook |

Quick start: `docker compose -f deploy/docker-compose.dev.yaml up -d`, then `cd apps/api && uv sync && uv run python -m app migrate && uv run python -m app api`. Frontends: `bun install && bun run dev`. See `AGENTS.md`, `deploy/DEPLOY.md`.
