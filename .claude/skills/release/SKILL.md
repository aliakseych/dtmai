---
name: release
description: Use when building images, deploying, or cutting a release.
---

# Release
- GitHub Actions: lint/test/build, push images to GHCR tagged with the commit SHA; actions pinned by SHA.
- Deploy: `deploy/DEPLOY.md`. On VPS: set `IMAGE_TAG`, `docker compose -f docker-compose.prod.yaml pull && up -d`; `migrate` runs first.
- Checklist: openapi.json fresh, migrations applied in staging, i18n parity green, backup taken, rollback = previous `IMAGE_TAG`.
