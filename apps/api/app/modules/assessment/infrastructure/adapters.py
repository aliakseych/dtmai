"""Adapters over other modules' public facades."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank import facade as bank
from app.modules.catalog import facade as catalog
from app.modules.identity.wiring import build_identity_service
from app.modules.learning import facade as learning
from app.modules.assessment.ports import Blueprint, Graded, Item, WeakSpot
from app.shared.entitlements import entitlements_for


def _item(d: Any) -> Item:
    return Item(d.id, d.subject_id, d.topic_id, d.type_id, d.kind, d.language, d.stem,
                list(d.media), dict(d.payload), d.passage_id or d.parent_id, [_item(c) for c in d.children])


def _flatten(dtos: Sequence[Any]) -> list[Item]:
    """passage_group stays one item (a single answerable unit) with its children embedded."""
    return [_item(d) for d in dtos]


def _bp(b: Any) -> Blueprint:
    return Blueprint(b.id, b.code, dict(b.names), b.kind, b.version, b.duration_min, list(b.sections))


class FacadeContent:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def blueprint(self, blueprint_id: UUID) -> Blueprint | None:
        b = await catalog.get_blueprint(self._s, blueprint_id)
        return _bp(b) if b else None

    async def blueprints(self) -> list[Blueprint]:
        out: list[Blueprint] = []
        for kind in ("official", "generated"):
            out += [_bp(b) for b in await catalog.list_blueprints(self._s, kind=kind, active=True)]
        return out

    async def items(self, ids: Sequence[UUID]) -> list[Item]:
        by_id = {i.id: i for i in _flatten(await bank.get_questions(self._s, list(ids)))}
        return [by_id[i] for i in ids if i in by_id]

    async def pick(
        self, *, subject_id: UUID, topic_ids: Sequence[UUID] | None, type_ids: Sequence[UUID] | None,
        language: str, n: int, exclude_ids: Sequence[UUID] = (),
    ) -> list[Item]:
        dtos = await bank.pick_questions(
            self._s, subject_id=subject_id, topic_ids=topic_ids or None, type_ids=type_ids or None,
            language=language, n=n, exclude_ids=exclude_ids,
        )
        return _flatten(dtos)[:n]

    async def grade(self, question_id: UUID, response: dict[str, Any]) -> Graded:
        r = await bank.grade(self._s, question_id, response)
        return Graded(r.correct, r.correct_response)

    async def weak_spots(self, user_id: UUID, subject_id: UUID) -> list[WeakSpot]:
        return [WeakSpot(w.topic_id, w.type_id) for w in await learning.weak_areas(self._s, user_id, subject_id, 5)]


class FacadeUsers:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def has_feature(self, user_id: UUID, feature: str) -> bool:
        return (await entitlements_for(user_id)).has(feature)

    async def target_lyceum_id(self, user_id: UUID) -> UUID | None:
        return (await build_identity_service(self._s).get_me(user_id)).target_lyceum_id
