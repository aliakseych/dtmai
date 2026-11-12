"""Public catalog facade. Other modules import only this."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank import facade as bank
from app.modules.catalog.application.service import CatalogService
from app.modules.catalog.domain import models as dom
from app.modules.catalog.infrastructure.repositories import SqlCatalogRepository
from app.shared.errors import NotFound


@dataclass(frozen=True, slots=True)
class SubjectDTO:
    id: UUID
    code: str
    names: dict[str, str]
    weight: float
    active: bool
    position: int


@dataclass(frozen=True, slots=True)
class TopicDTO:
    id: UUID
    subject_id: UUID
    parent_id: UUID | None
    code: str | None
    names: dict[str, str]
    position: int
    active: bool


@dataclass(frozen=True, slots=True)
class QuestionTypeDTO:
    id: UUID
    code: str
    kind: str
    names: dict[str, str]
    config: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BlueprintDTO:
    id: UUID
    code: str
    names: dict[str, str]
    kind: str
    version: int
    duration_min: int
    sections: list[dict[str, Any]]
    status: str
    source_id: UUID | None


@dataclass(frozen=True, slots=True)
class LessonDTO:
    id: UUID
    names: dict[str, str]
    title: str
    topic_ids: list[UUID]
    effective_topic_ids: list[UUID]
    type_ids: list[UUID]
    question_count: int
    legendary: bool
    pool: int
    theory: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class UnitDTO:
    id: UUID
    names: dict[str, str]
    title: str
    lessons: list[LessonDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PathDTO:
    id: UUID
    subject_id: UUID
    language: str
    names: dict[str, str]
    units: list[UnitDTO]


@dataclass(frozen=True, slots=True)
class ReferenceSheetDTO:
    subject_id: UUID
    locale: str
    content: str
    source: str
    updated_at: datetime


def service(session: AsyncSession) -> CatalogService:
    return CatalogService(SqlCatalogRepository(session))


def _subject(r: dict[str, Any]) -> SubjectDTO:
    return SubjectDTO(r["id"], r["code"], r["names"], r["weight"], r["active"], r["position"])


def _topic(r: dict[str, Any]) -> TopicDTO:
    return TopicDTO(
        r["id"], r["subject_id"], r["parent_id"], r["code"], r["names"], r["position"], r["active"]
    )


def _bp(r: dict[str, Any]) -> BlueprintDTO:
    return BlueprintDTO(
        r["id"],
        r["code"],
        r["names"],
        r["kind"],
        r["version"],
        r["duration_min"],
        r["sections"],
        r["status"],
        r["source_id"],
    )


async def get_subject(session: AsyncSession, id: UUID) -> SubjectDTO:
    return _subject(await service(session).require("subject", id))


async def list_subjects(session: AsyncSession, *, active_only: bool = True) -> list[SubjectDTO]:
    rows = await SqlCatalogRepository(session).list("subject")
    return [_subject(r) for r in rows if r["active"] or not active_only]


async def get_reference(
    session: AsyncSession, subject_id: UUID, locale: str = "uz-Latn"
) -> ReferenceSheetDTO | None:
    """Active reference sheet of a subject in the best available locale, or None."""
    row = await service(session).get_reference(subject_id)
    if row is None or not row["active"]:
        return None
    contents: dict[str, str] = row["contents"]
    loc = next((k for k in (locale, "uz-Latn", "ru", "en", "uz-Cyrl") if contents.get(k)), None)
    if loc is None:
        return None
    return ReferenceSheetDTO(subject_id, loc, contents[loc], row["source"], row["updated_at"])


async def get_topic(session: AsyncSession, id: UUID) -> TopicDTO:
    return _topic(await service(session).require("topic", id))


async def list_topics(session: AsyncSession, subject_id: UUID) -> list[TopicDTO]:
    return [
        _topic(r) for r in await SqlCatalogRepository(session).list("topic", subject_id=subject_id)
    ]


async def get_question_type(session: AsyncSession, id: UUID) -> QuestionTypeDTO:
    r = await service(session).require("question_type", id)
    return QuestionTypeDTO(r["id"], r["code"], r["kind"], r["names"], r["config"])


async def list_question_types(session: AsyncSession) -> list[QuestionTypeDTO]:
    return [
        QuestionTypeDTO(r["id"], r["code"], r["kind"], r["names"], r["config"])
        for r in await SqlCatalogRepository(session).list("question_type")
        if r["active"]
    ]


async def expand_topic_ids(
    session: AsyncSession, subject_id: UUID, topic_ids: Sequence[UUID]
) -> list[UUID]:
    """Topic ids plus all descendants."""
    pm = await service(session)._parent_map(subject_id)
    return [UUID(x) for x in dom.descendants(pm, [str(t) for t in topic_ids])]


async def get_blueprint(session: AsyncSession, id: UUID) -> BlueprintDTO:
    return _bp(await service(session).require("blueprint", id))


async def list_blueprints(
    session: AsyncSession, *, kind: str | None = None, active: bool = True
) -> list[BlueprintDTO]:
    """Latest published version per code (active=True) or every row."""
    rows = await SqlCatalogRepository(session).list("blueprint")
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    if active:
        latest: dict[str, dict[str, Any]] = {}
        for r in rows:
            if (
                r["status"] == "published"
                and r["version"] > latest.get(r["code"], {"version": 0})["version"]
            ):
                latest[r["code"]] = r
        rows = list(latest.values())
    return [_bp(r) for r in rows]


async def get_path(
    session: AsyncSession,
    subject_id: UUID,
    language: str,
    *,
    locale: str = "uz-Latn",
    include_draft: bool = False,
) -> PathDTO | None:
    """Published path with only learnable lessons (verified pool >= max(min_pool, question_count))."""
    repo = SqlCatalogRepository(session)
    paths = await repo.list("path", subject_id=subject_id, language=language)
    if not paths or (paths[0]["status"] != "published" and not include_draft):
        return None
    p = paths[0]
    min_pool = bank.content_min_pool()
    units: list[UnitDTO] = []
    for u in await repo.list("unit", path_id=p["id"]):
        lessons: list[LessonDTO] = []
        for le in await repo.list("lesson", unit_id=u["id"]):
            topics = [UUID(t) for t in le["topic_ids"]]
            eff = await expand_topic_ids(session, subject_id, topics) if topics else []
            types = [UUID(t) for t in le["type_ids"]]
            pool = await bank.count_verified(
                session,
                subject_id=subject_id,
                topic_ids=eff or None,
                type_ids=types or None,
                language=language,
            )
            if dom.lesson_visible(pool, le["question_count"], min_pool) or include_draft:
                lessons.append(
                    LessonDTO(
                        le["id"],
                        le["names"],
                        dom.pick_name(le["names"], locale),
                        topics,
                        eff,
                        types,
                        le["question_count"],
                        le["legendary"],
                        pool,
                        list(le.get("theory") or []),
                    )
                )
        if lessons:
            units.append(UnitDTO(u["id"], u["names"], dom.pick_name(u["names"], locale), lessons))
    return PathDTO(p["id"], subject_id, language, p["names"], units)


async def get_or_create_source(
    session: AsyncSession, *, code: str, name: str, year: int | None = None, kind: str = "custom"
) -> UUID:
    repo = SqlCatalogRepository(session)
    for r in await repo.list("question_base", code=code):
        return r["id"]
    row = await service(session).create(
        "question_base", {"code": code, "names": {"en": name}, "kind": kind, "year": year}, "system"
    )
    return row["id"]


async def require_subject_exists(session: AsyncSession, id: UUID) -> None:
    if await SqlCatalogRepository(session).get("subject", id) is None:
        raise NotFound(f"subject {id} not found")
