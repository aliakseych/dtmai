"""Field-of-study lookups exposed to other modules (identity derives subjects through this)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lyceums.infrastructure.repositories import SqlFields


class FieldCatalog:
    def __init__(self, session: AsyncSession) -> None:
        self._fields = SqlFields(session)

    async def subjects_for(self, field_code: str) -> list[UUID] | None:
        return await self._fields.subjects_for(field_code)

    async def offered_fields(self, lyceum_ids: list[UUID]) -> dict[UUID, set[str]]:
        return {k: set(v) for k, v in (await self._fields.codes_by_lyceum(lyceum_ids)).items()}


def build_field_catalog(session: AsyncSession) -> FieldCatalog:
    return FieldCatalog(session)
