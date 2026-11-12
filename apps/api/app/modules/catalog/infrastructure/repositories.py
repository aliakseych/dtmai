from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.infrastructure.orm import ENTITIES, AuditRow, BlueprintRow
from app.shared.errors import Conflict


def _d(row: Any) -> dict[str, Any]:
    return {c.key: getattr(row, c.key) for c in row.__mapper__.column_attrs}


class SqlCatalogRepository:
    """Generic dict-in/dict-out repository over the catalog tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, entity: str, id: UUID) -> dict[str, Any] | None:
        row = await self.s.get(ENTITIES[entity], id)
        return _d(row) if row else None

    async def list(self, entity: str, **eq: Any) -> list[dict[str, Any]]:
        model = ENTITIES[entity]
        q = select(model)
        for k, v in eq.items():
            q = q.where(getattr(model, k) == v)
        order = [getattr(model, "position")] if hasattr(model, "position") else []
        q = q.order_by(*order, getattr(model, "id"))
        return [_d(r) for r in (await self.s.scalars(q)).all()]

    async def insert(self, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        row = ENTITIES[entity](**data)
        self.s.add(row)
        await self._flush()
        return _d(row)

    async def update(self, entity: str, id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        row = await self.s.get(ENTITIES[entity], id)
        assert row is not None
        for k, v in data.items():
            setattr(row, k, v)
        await self._flush()
        return _d(row)

    async def delete(self, entity: str, id: UUID) -> None:
        await self.s.execute(delete(ENTITIES[entity]).where(ENTITIES[entity].id == id))  # type: ignore[attr-defined]
        await self._flush()

    async def _flush(self) -> None:
        try:
            await self.s.flush()
        except IntegrityError as e:
            await self.s.rollback()
            raise Conflict(
                "Constraint violated (duplicate code/language or referenced row)",
                code="catalog.conflict",
            ) from e

    async def max_position(self, entity: str, **eq: Any) -> int:
        model = ENTITIES[entity]
        q = select(func.coalesce(func.max(model.position), -1))  # type: ignore[attr-defined]
        for k, v in eq.items():
            q = q.where(getattr(model, k) == v)
        return int(await self.s.scalar(q) or -1)

    async def max_version(self, code: str) -> int:
        return int(
            await self.s.scalar(
                select(func.coalesce(func.max(BlueprintRow.version), 0)).where(
                    BlueprintRow.code == code
                )
            )
            or 0
        )

    async def add_audit(self, **fields: Any) -> None:
        self.s.add(AuditRow(**fields))
        await self.s.flush()

    async def list_audit(
        self, entity: str | None, entity_id: UUID | None, limit: int
    ) -> list[dict[str, Any]]:
        q = select(AuditRow).order_by(AuditRow.id.desc()).limit(limit)
        if entity:
            q = q.where(AuditRow.entity == entity)
        if entity_id:
            q = q.where(AuditRow.entity_id == entity_id)
        return [_d(r) for r in (await self.s.scalars(q)).all()]
