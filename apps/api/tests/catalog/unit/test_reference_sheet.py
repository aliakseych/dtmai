from typing import Any
from uuid import UUID, uuid4

import pytest

from app.modules.catalog.application.service import CatalogService
from app.modules.catalog.domain import models as dom
from app.shared.errors import NotFound, ValidationFailed

NAMES = {"uz-Latn": "Matematika", "ru": "Математика"}


class MemRepo:
    """Dict-backed CatalogRepository covering what reference sheets need."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[UUID, dict[str, Any]]] = {}
        self.audit: list[dict[str, Any]] = []

    async def get(self, entity: str, id: UUID) -> dict[str, Any] | None:
        return self.rows.get(entity, {}).get(id)

    async def list(self, entity: str, **eq: Any) -> list[dict[str, Any]]:
        return [
            r
            for r in self.rows.get(entity, {}).values()
            if all(r.get(k) == v for k, v in eq.items())
        ]

    async def insert(self, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        self.rows.setdefault(entity, {})[data["id"]] = dict(data)
        return dict(data)

    async def update(self, entity: str, id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        self.rows[entity][id].update(data)
        return dict(self.rows[entity][id])

    async def delete(self, entity: str, id: UUID) -> None:
        self.rows[entity].pop(id)

    async def max_position(self, entity: str, **eq: Any) -> int:
        return 0

    async def add_audit(self, **fields: Any) -> None:
        self.audit.append(fields)


def make() -> tuple[CatalogService, MemRepo, UUID]:
    repo = MemRepo()
    sid = uuid4()
    repo.rows["subject"] = {sid: {"id": sid, "code": "math", "names": NAMES, "active": True}}
    return CatalogService(repo), repo, sid  # type: ignore[arg-type]


def test_validate_normalises_contents():
    d = dom.validate_entity(
        "reference_sheet", {"contents": {"uz-Latn": "  $a^2$  ", "ru": "   "}, "source": " s "}
    )
    assert d["contents"] == {"uz-Latn": "$a^2$"}
    assert d["source"] == "s"
    assert d["active"] is True


@pytest.mark.parametrize(
    "data",
    [
        {"contents": {}},
        {"contents": {"xx": "a"}},
        {"contents": {"ru": "   "}},
        {"contents": {"ru": "a" * (dom.MAX_REFERENCE_CHARS + 1)}},
        {"contents": {"ru": "a"}, "source": "s" * 501},
        {"contents": {"ru": "a"}, "active": "yes"},
    ],
)
def test_validate_rejects(data: dict[str, Any]):
    with pytest.raises(dom.Invalid):
        dom.validate_entity("reference_sheet", data)


async def test_upsert_creates_then_replaces_single_row():
    svc, repo, sid = make()
    first = await svc.upsert_reference(sid, {"contents": {"ru": "v1"}}, "admin")
    second = await svc.upsert_reference(sid, {"contents": {"ru": "v2"}, "source": "x"}, "admin")
    assert first["id"] == second["id"]
    assert len(repo.rows["reference_sheet"]) == 1
    got = await svc.get_reference(sid)
    assert got and got["contents"] == {"ru": "v2"} and got["source"] == "x"
    assert [a["action"] for a in repo.audit] == ["create", "update"]


async def test_upsert_unknown_subject_is_not_found():
    svc, _, _ = make()
    with pytest.raises(NotFound):
        await svc.upsert_reference(uuid4(), {"contents": {"ru": "a"}}, None)


async def test_upsert_invalid_content_is_validation_error():
    svc, _, sid = make()
    with pytest.raises(ValidationFailed):
        await svc.upsert_reference(sid, {"contents": {}}, None)


async def test_subject_id_is_frozen():
    svc, _, sid = make()
    row = await svc.upsert_reference(sid, {"contents": {"ru": "a"}}, None)
    with pytest.raises(ValidationFailed):
        await svc.update("reference_sheet", row["id"], {"subject_id": uuid4()}, None)


async def test_delete_reference():
    svc, _, sid = make()
    with pytest.raises(NotFound):
        await svc.delete_reference(sid, None)
    await svc.upsert_reference(sid, {"contents": {"ru": "a"}}, None)
    await svc.delete_reference(sid, None)
    assert await svc.get_reference(sid) is None
