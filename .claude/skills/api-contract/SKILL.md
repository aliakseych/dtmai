---
name: api-contract
description: Use when adding or changing an HTTP endpoint, DTO, or error shape in apps/api, or regenerating clients.
---

# API contract
- FastAPI generates the contract: `apps/api/openapi/openapi.json` (owner: apps/api).
- Agree operation, DTOs, auth, status codes and errors first. Routes live in `app/interfaces/http/v1/<m>.py`; DTOs are pydantic models there, never domain objects.
- Set `operation_id` (`<module>_<action>`), `tags=[module]`, response models and `responses` for errors (problem+json).
- After any change: `bun run gen:api`; commit openapi.json + `packages/api-client`. Flutter: openapi-generator dart-dio from the same file.
- CI fails if openapi.json is stale. Avoid breaking changes; additive first.
