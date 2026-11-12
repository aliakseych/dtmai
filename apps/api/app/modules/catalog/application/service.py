from datetime import UTC, date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.modules.catalog.domain import models as dom
from app.modules.catalog.ports import CatalogRepository
from app.shared.errors import Conflict, NotFound, ValidationFailed
from app.shared.ids import new_id


def jsonable(v: Any) -> Any:
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime | date):
        return v.isoformat()
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    if isinstance(v, list | tuple):
        return [jsonable(x) for x in v]
    return v


# immutable after creation
_FROZEN = {
    "subject": (),
    "topic": ("subject_id",),
    "path": ("subject_id",),
    "unit": ("path_id",),
    "lesson": ("unit_id",),
    "blueprint": ("code", "version", "status", "published_at"),
}
# system-managed columns that API patches may not touch
_SYSTEM = {"id", "version", "status", "published_at"}


class CatalogService:
    def __init__(self, repo: CatalogRepository) -> None:
        self.repo = repo

    async def _validate(self, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            return dom.validate_entity(entity, data)
        except dom.Invalid as e:
            raise ValidationFailed(str(e)) from e

    async def require(self, entity: str, id: UUID) -> dict[str, Any]:
        row = await self.repo.get(entity, id)
        if row is None:
            raise NotFound(f"{entity} {id} not found")
        return row

    async def _check_refs(self, entity: str, d: dict[str, Any]) -> None:
        if entity in ("topic", "path"):
            await self.require("subject", d["subject_id"])
        if entity == "topic" and d.get("parent_id"):
            parent = await self.require("topic", d["parent_id"])
            if parent["subject_id"] != d["subject_id"]:
                raise ValidationFailed("parent topic belongs to another subject")
            if d.get("id") and dom.creates_cycle(
                await self._parent_map(d["subject_id"]), str(d["id"]), str(d["parent_id"])
            ):
                raise ValidationFailed("topic parent would create a cycle")
        if entity == "unit":
            await self.require("path", d["path_id"])
        if entity == "lesson":
            unit = await self.require("unit", d["unit_id"])
            path = await self.require("path", unit["path_id"])
            await self._check_selectors(path["subject_id"], d)
        if entity == "blueprint":
            for s in d["sections"]:
                await self.require("subject", UUID(s["subject_id"]))

    async def _parent_map(self, subject_id: UUID) -> dict[str, str | None]:
        return {
            str(t["id"]): (str(t["parent_id"]) if t["parent_id"] else None)
            for t in await self.repo.list("topic", subject_id=subject_id)
        }

    async def _check_selectors(self, subject_id: UUID, d: dict[str, Any]) -> None:
        if d["topic_ids"]:
            known = set((await self._parent_map(subject_id)))
            bad = [t for t in d["topic_ids"] if t not in known]
            if bad:
                raise ValidationFailed(f"topic_ids not in this subject: {bad}")
        for t in d["type_ids"]:
            await self.require("question_type", UUID(t))

    async def _audit(
        self, actor: str | None, action: str, entity: str, eid: UUID, before: Any, after: Any
    ) -> None:
        await self.repo.add_audit(
            actor=actor,
            action=action,
            entity=entity,
            entity_id=eid,
            before=jsonable(before),
            after=jsonable(after),
        )

    async def create(self, entity: str, data: dict[str, Any], actor: str | None) -> dict[str, Any]:
        d = await self._validate(entity, data)
        d["id"] = new_id()
        if "position" in d and d.get("position") is None:
            d.pop("position")
        if entity == "blueprint":
            d.update(version=0, status="draft", published_at=None)
        if entity == "path":
            d["status"] = "draft"
        await self._check_refs(entity, d)
        if "position" not in d and entity in {
            "subject",
            "topic",
            "question_type",
            "path",
            "unit",
            "lesson",
            "question_base",
        }:
            scope = {k: d[k] for k in ("subject_id", "path_id", "unit_id") if k in d}
            d["position"] = await self.repo.max_position(entity, **scope) + 1
        row = await self.repo.insert(entity, d)
        await self._audit(actor, "create", entity, row["id"], None, row)
        return row

    async def update(
        self, entity: str, id: UUID, patch: dict[str, Any], actor: str | None
    ) -> dict[str, Any]:
        before = await self.require(entity, id)
        if entity == "blueprint" and before["status"] == "published":
            raise Conflict(
                "Published blueprints are immutable; clone to a draft",
                code="catalog.blueprint_published",
            )
        frozen = set(_FROZEN.get(entity, ())) | _SYSTEM
        if bad := frozen & patch.keys():
            raise ValidationFailed(f"fields are not editable: {sorted(bad)}")
        merged = await self._validate(entity, {**before, **patch})
        await self._check_refs(entity, merged)
        row = await self.repo.update(entity, id, {k: v for k, v in merged.items() if k in patch})
        await self._audit(actor, "update", entity, id, before, row)
        return row

    async def delete(self, entity: str, id: UUID, actor: str | None) -> None:
        before = await self.require(entity, id)
        if entity == "blueprint" and before["status"] == "published":
            raise Conflict(
                "Published blueprints cannot be deleted; deactivate via a new version",
                code="catalog.blueprint_published",
            )
        await self.repo.delete(entity, id)
        await self._audit(actor, "delete", entity, id, before, None)

    async def reorder(
        self, entity: str, ids: list[UUID], actor: str | None, **scope: Any
    ) -> list[dict[str, Any]]:
        rows = await self.repo.list(entity, **scope)
        if not dom.sequence_is_permutation([r["id"] for r in rows], ids):
            raise ValidationFailed("ids must be exactly the current sibling set")
        for pos, i in enumerate(ids):
            await self.repo.update(entity, i, {"position": pos})
        await self._audit(
            actor, "reorder", entity, ids[0] if ids else new_id(), None, {"ids": ids, **scope}
        )
        return await self.repo.list(entity, **scope)

    # ---- path / blueprint lifecycle -----------------------------------------------------
    async def set_path_status(self, id: UUID, status: str, actor: str | None) -> dict[str, Any]:
        before = await self.require("path", id)
        row = await self.repo.update("path", id, {"status": status})
        await self._audit(actor, status, "path", id, before, row)
        return row

    async def publish_blueprint(self, id: UUID, actor: str | None) -> dict[str, Any]:
        bp = await self.require("blueprint", id)
        if bp["status"] == "published":
            raise Conflict("Already published", code="catalog.blueprint_published")
        v = await self.repo.max_version(bp["code"]) + 1
        row = await self.repo.update(
            "blueprint",
            id,
            {"status": "published", "version": v, "published_at": datetime.now(UTC)},
        )
        await self._audit(actor, "publish", "blueprint", id, bp, row)
        return row

    async def clone_blueprint(self, id: UUID, actor: str | None) -> dict[str, Any]:
        bp = await self.require("blueprint", id)
        data = {
            k: bp[k] for k in ("code", "names", "kind", "sections", "duration_min", "source_id")
        }
        return await self.create("blueprint", data, actor)

    async def audit(
        self, entity: str | None, entity_id: UUID | None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return await self.repo.list_audit(entity, entity_id, limit)
