"""Content adapter over the bank and catalog public facades (resolved at call time)."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank import facade as bank
from app.modules.catalog import facade as catalog
from app.modules.learning.ports import Graded, Item, LessonRef


def _item(d: Any) -> Item:
    return Item(
        d.id,
        d.subject_id,
        d.topic_id,
        d.type_id,
        d.kind,
        d.language,
        float(d.difficulty),
        d.stem,
        list(d.media),
        dict(d.payload),
        d.passage_id or d.parent_id,
        d.source_id is not None,
        [_item(c) for c in d.children],
    )


def _flatten(dtos: Sequence[Any]) -> list[Item]:
    """passage_group stays one item (a single answerable unit) with its children embedded."""
    return [_item(d) for d in dtos]


class FacadeContent:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def items(self, ids: Sequence[UUID]) -> list[Item]:
        by_id = {i.id: i for i in _flatten(await bank.get_questions(self._s, list(ids)))}
        return [by_id[i] for i in ids if i in by_id]

    async def pick(
        self,
        *,
        subject_id: UUID,
        topic_ids: Sequence[UUID] | None,
        type_ids: Sequence[UUID] | None,
        language: str,
        n: int,
        exclude_ids: Sequence[UUID] = (),
        difficulty: float | None = None,
    ) -> list[Item]:
        dtos = await bank.pick_questions(
            self._s,
            subject_id=subject_id,
            topic_ids=topic_ids or None,
            type_ids=type_ids or None,
            language=language,
            n=n,
            exclude_ids=exclude_ids,
            difficulty=difficulty,
        )
        return _flatten(dtos)[:n]

    async def grade(self, question_id: UUID, response: dict[str, Any]) -> Graded:
        r = await bank.grade(self._s, question_id, response)
        return Graded(r.correct, r.correct_response)

    async def lesson(self, lesson_id: UUID, language: str | None) -> LessonRef | None:
        """Find a lesson by id by scanning the learning path(s) of active subjects."""
        for subject in await catalog.list_subjects(self._s):
            lang = language or "uz"
            path = await catalog.get_path(self._s, subject.id, lang)
            if path is None:
                continue
            for unit in path.units:
                for ls in unit.lessons:
                    if ls.id == lesson_id:
                        return LessonRef(
                            ls.id,
                            subject.id,
                            list(ls.effective_topic_ids),
                            list(ls.type_ids),
                            ls.question_count or 10,
                            lang,
                            len(path.units),
                            [[le.id for le in u.lessons] for u in path.units],
                        )
        return None

    async def unit_count(self, subject_id: UUID, language: str) -> int:
        path = await catalog.get_path(self._s, subject_id, language)
        return len(path.units) if path else 0
