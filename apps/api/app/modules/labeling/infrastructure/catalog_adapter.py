"""Defensive adapter over the catalog facade (the only place labeling talks to catalog)."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog import facade as catalog


@dataclass(frozen=True, slots=True)
class SubjectRef:
    id: UUID
    code: str
    names: dict[str, str]


@dataclass(frozen=True, slots=True)
class TypeInfo:
    id: UUID
    kind: str
    prompt_template: str | None
    config: dict[str, Any]


def _s(obj: Any, *names: str, default: Any = None) -> Any:
    for n in names:
        if isinstance(obj, dict) and n in obj:
            return obj[n]
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


async def list_subjects(session: AsyncSession) -> list[SubjectRef]:
    out: list[SubjectRef] = []
    for s in await catalog.list_subjects(session):
        names = _s(s, "names", "name", default={}) or {}
        out.append(
            SubjectRef(
                _s(s, "id"),
                str(_s(s, "code", "slug", default="")),
                names if isinstance(names, dict) else {"en": str(names)},
            )
        )
    return out


async def get_or_create_source(
    session: AsyncSession, *, code: str, name: str, year: int | None
) -> UUID:
    kind = "previous_year" if year else "custom"
    return await catalog.get_or_create_source(session, code=code, name=name, year=year, kind=kind)


async def get_question_type(session: AsyncSession, type_id: UUID) -> TypeInfo | None:
    getter = getattr(catalog, "get_question_type", None)
    if getter is None:
        return None
    qt = await getter(session, type_id)
    if qt is None:
        return None
    return TypeInfo(
        type_id,
        str(_s(qt, "kind", default="")),
        _s(qt, "generation_prompt_template", "prompt_template"),
        _s(qt, "config", default={}) or {},
    )


async def topic_label(session: AsyncSession, topic_id: UUID) -> str:
    t = await catalog.get_topic(session, topic_id)
    names = _s(t, "names", "name", default=None)
    if isinstance(names, dict):
        return str(names.get("en") or next(iter(names.values()), topic_id))
    return str(names or _s(t, "code", "slug", default=topic_id))


async def find_type_ids(session: AsyncSession) -> dict[str, UUID]:
    """kind -> first question type id, when the catalog facade can list types (else empty)."""
    lister = getattr(catalog, "list_question_types", None)
    if lister is None:
        return {}
    out: dict[str, UUID] = {}
    for qt in await lister(session):
        kind = str(_s(qt, "kind", default=""))
        if kind and kind not in out:
            out[kind] = _s(qt, "id")
    return out


async def first_topic(session: AsyncSession, subject_id: UUID) -> UUID | None:
    lister = getattr(catalog, "list_topics", None)
    if lister is None:
        return None
    topics = await lister(session, subject_id)
    return _s(topics[0], "id") if topics else None


async def ordered_topics(session: AsyncSession, subject_id: UUID) -> list[tuple[UUID, str]]:
    """Active topics in a stable order (id) with display labels; index+1 is the number shown to the model."""
    lister = getattr(catalog, "list_topics", None)
    if lister is None:
        return []
    out: list[tuple[UUID, str]] = []
    for t in sorted(await lister(session, subject_id), key=lambda x: str(_s(x, "id"))):
        if not _s(t, "active", default=True):
            continue
        names = _s(t, "names", default={}) or {}
        label = names.get("en") or next(iter(names.values()), "") if isinstance(names, dict) else str(names)
        out.append((_s(t, "id"), str(label or _s(t, "code", default=""))))
    return out
