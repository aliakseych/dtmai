from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    ColumnElement,
    MetaData,
    String,
    Table,
    Uuid,
    and_,
    case,
    cast,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank.domain.models import LEVEL_BOUNDS, Passage, Question, QuestionFilter
from app.modules.bank.infrastructure.orm import (
    AuditRow,
    ExplanationRow,
    PassageRow,
    ProcessedEventRow,
    QuestionRow,
    ReportRow,
)

_Q_FIELDS = (
    "id subject_id topic_id type_id kind language stem payload answer difficulty media passage_id "
    "parent_id source_id source_ref translation_group_id status answer_official attempts "
    "correct_count report_count created_by created_at updated_at"
).split()

# Read-only reference to the catalog's base registry (no ORM import: bank stays below catalog).
_BASES = Table(
    "question_bases",
    MetaData(),
    Column("id", Uuid),
    Column("archived", Boolean),
    schema="catalog",
)


def _base_visible() -> ColumnElement[bool]:
    """Learner-visible: no base, or the base is not archived."""
    archived = select(_BASES.c.id).where(_BASES.c.archived.is_(True))
    return or_(QuestionRow.source_id.is_(None), QuestionRow.source_id.not_in(archived))


def _to_domain(r: QuestionRow) -> Question:
    return Question(**{f: getattr(r, f) for f in _Q_FIELDS})


def _apply(r: QuestionRow, q: Question) -> None:
    for f in _Q_FIELDS:
        if f in ("created_at", "updated_at"):
            continue
        setattr(r, f, getattr(q, f))


def _passage(r: PassageRow) -> Passage:
    return Passage(r.id, r.language, r.text, r.title, list(r.media or []), r.source_id)


def _scope(
    subject_id: UUID,
    topic_ids: Sequence[UUID] | None,
    type_ids: Sequence[UUID] | None,
    language: str,
    statuses: Sequence[str],
    source_id: UUID | None = None,
    level: str | None = None,
) -> list[ColumnElement[bool]]:
    c: list[ColumnElement[bool]] = [
        QuestionRow.subject_id == subject_id,
        QuestionRow.language == language,
        QuestionRow.status.in_(list(statuses)),
        QuestionRow.parent_id.is_(None),  # group children are served through their parent
        _base_visible(),
    ]
    if topic_ids:
        c.append(QuestionRow.topic_id.in_(list(topic_ids)))
    if type_ids:
        c.append(QuestionRow.type_id.in_(list(type_ids)))
    if source_id is not None:
        c.append(QuestionRow.source_id == source_id)
    if level is not None:
        lo, hi = LEVEL_BOUNDS[level]
        if lo is not None:
            c.append(QuestionRow.difficulty >= lo)
        if hi is not None:
            c.append(QuestionRow.difficulty < hi)
    return c


class SqlQuestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def add(self, q: Question) -> None:
        row = QuestionRow()
        _apply(row, q)
        self.s.add(row)
        await self.s.flush()

    async def get_many(self, ids: Sequence[UUID]) -> list[Question]:
        if not ids:
            return []
        rows = (
            await self.s.scalars(select(QuestionRow).where(QuestionRow.id.in_(list(ids))))
        ).all()
        by_id = {r.id: r for r in rows}
        return [_to_domain(by_id[i]) for i in ids if i in by_id]

    async def save(self, q: Question) -> None:
        row = await self.s.get(QuestionRow, q.id)
        if row is None:
            return
        _apply(row, q)
        await self.s.flush()

    async def pick(
        self,
        *,
        subject_id: UUID,
        topic_ids: Sequence[UUID] | None,
        type_ids: Sequence[UUID] | None,
        language: str,
        n: int,
        exclude_ids: Sequence[UUID],
        difficulty: float | None,
        statuses: Sequence[str],
        source_id: UUID | None = None,
        level: str | None = None,
    ) -> list[Question]:
        stmt = select(QuestionRow).where(
            *_scope(subject_id, topic_ids, type_ids, language, statuses, source_id, level)
        )
        if exclude_ids:
            stmt = stmt.where(QuestionRow.id.not_in(list(exclude_ids)))
        if difficulty is not None:
            # nearest-difficulty first, random among near-equals
            stmt = stmt.order_by(
                func.round((func.abs(QuestionRow.difficulty - difficulty) / 50.0)), func.random()
            )
        else:
            stmt = stmt.order_by(func.random())
        rows = (await self.s.scalars(stmt.limit(max(n, 0)))).all()
        return [_to_domain(r) for r in rows]

    async def count(
        self,
        *,
        subject_id: UUID,
        topic_ids: Sequence[UUID] | None,
        type_ids: Sequence[UUID] | None,
        language: str,
        statuses: Sequence[str],
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(QuestionRow)
            .where(*_scope(subject_id, topic_ids, type_ids, language, statuses))
        )
        return int(await self.s.scalar(stmt) or 0)

    async def facets(
        self, subject_id: UUID, language: str, solved_ids: Sequence[UUID]
    ) -> list[tuple[UUID, UUID, UUID | None, str, int, int]]:
        """Verified top-level questions grouped by (topic, type, source, level) with the total
        and how many of them are in `solved_ids`."""
        d = QuestionRow.difficulty
        level = case((d < 1100, "easy"), (d < 1350, "medium"), else_="hard")
        solved = func.count().filter(QuestionRow.id.in_(list(solved_ids)))
        rows = await self.s.execute(
            select(
                QuestionRow.topic_id,
                QuestionRow.type_id,
                QuestionRow.source_id,
                level,
                func.count(),
                solved,
            )
            .where(*_scope(subject_id, None, None, language, ("verified",)))
            .group_by(QuestionRow.topic_id, QuestionRow.type_id, QuestionRow.source_id, level)
        )
        return [(t, ty, s, lv, int(n), int(sv)) for t, ty, s, lv, n, sv in rows.all()]

    async def search(
        self, f: QuestionFilter, limit: int, offset: int
    ) -> tuple[list[Question], int]:
        conds: list[ColumnElement[bool]] = []
        for col, val in (
            (QuestionRow.subject_id, f.subject_id),
            (QuestionRow.topic_id, f.topic_id),
            (QuestionRow.type_id, f.type_id),
            (QuestionRow.language, f.language),
            (QuestionRow.status, f.status),
            (QuestionRow.source_id, f.source_id),
            (QuestionRow.kind, f.kind),
        ):
            if val is not None:
                conds.append(col == val)
        if f.q:
            like = f"%{f.q.replace('%', r'\%').replace('_', r'\_')}%"
            conds.append(
                or_(QuestionRow.stem.ilike(like), cast(QuestionRow.id, String).ilike(like))
            )
        if f.reported:
            conds.append(QuestionRow.report_count > 0)
        if f.learner_visible:
            conds.append(_base_visible())
        where = and_(*conds) if conds else True
        total = int(
            await self.s.scalar(select(func.count()).select_from(QuestionRow).where(where)) or 0
        )
        rows = (
            await self.s.scalars(
                select(QuestionRow)
                .where(where)
                .order_by(QuestionRow.created_at.desc(), QuestionRow.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return [_to_domain(r) for r in rows], total

    async def bulk_set_status(self, ids: Sequence[UUID], status: str) -> int:
        if not ids:
            return 0
        res = await self.s.execute(
            update(QuestionRow).where(QuestionRow.id.in_(list(ids))).values(status=status)
        )
        return int(getattr(res, "rowcount", 0) or 0)

    async def coverage(
        self, subject_id: UUID | None, language: str | None
    ) -> list[tuple[UUID, UUID, UUID, str, int]]:
        conds: list[ColumnElement[bool]] = [
            QuestionRow.status == "verified",
            QuestionRow.parent_id.is_(None),
        ]
        if subject_id is not None:
            conds.append(QuestionRow.subject_id == subject_id)
        if language is not None:
            conds.append(QuestionRow.language == language)
        stmt = (
            select(
                QuestionRow.subject_id,
                QuestionRow.topic_id,
                QuestionRow.type_id,
                QuestionRow.language,
                func.count(),
            )
            .where(*conds)
            .group_by(
                QuestionRow.subject_id,
                QuestionRow.topic_id,
                QuestionRow.type_id,
                QuestionRow.language,
            )
        )
        return [(a, b, c, d, int(e)) for a, b, c, d, e in (await self.s.execute(stmt)).all()]

    async def add_report(self, question_id: UUID, user_id: UUID, reason: str) -> int:
        await self.s.execute(
            pg_insert(ReportRow)
            .values(question_id=question_id, user_id=user_id, reason=reason[:500])
            .on_conflict_do_nothing(index_elements=["question_id", "user_id"])
        )
        n = int(
            await self.s.scalar(
                select(func.count())
                .select_from(ReportRow)
                .where(ReportRow.question_id == question_id)
            )
            or 0
        )
        await self.s.execute(
            update(QuestionRow).where(QuestionRow.id == question_id).values(report_count=n)
        )
        return n

    async def claim_event(self, event_id: UUID) -> bool:
        res = await self.s.execute(
            pg_insert(ProcessedEventRow)
            .values(event_id=event_id)
            .on_conflict_do_nothing(index_elements=["event_id"])
        )
        return bool(getattr(res, "rowcount", 0))

    async def record_attempt(self, question_id: UUID, correct: bool) -> None:
        await self.s.execute(
            update(QuestionRow)
            .where(QuestionRow.id == question_id)
            .values(
                attempts=QuestionRow.attempts + 1,
                correct_count=QuestionRow.correct_count + (1 if correct else 0),
            )
        )

    async def upsert_explanation(
        self, question_id: UUID, locale: str, text: str, model: str
    ) -> None:
        stmt = pg_insert(ExplanationRow).values(
            question_id=question_id, locale=locale, text=text, model=model
        )
        await self.s.execute(
            stmt.on_conflict_do_update(
                index_elements=["question_id", "locale"],
                set_={
                    "text": stmt.excluded.text,
                    "model": stmt.excluded.model,
                    "updated_at": func.now(),
                },
            )
        )

    async def get_explanation(self, question_id: UUID, locale: str) -> str | None:
        return await self.s.scalar(
            select(ExplanationRow.text).where(
                ExplanationRow.question_id == question_id, ExplanationRow.locale == locale
            )
        )

    async def add_audit(
        self,
        actor: str | None,
        action: str,
        entity_id: UUID | None,
        before: Any,
        after: Any,
        reason: str = "",
    ) -> None:
        self.s.add(
            AuditRow(
                actor=actor,
                action=action,
                entity_id=entity_id,
                before=before,
                after=after,
                reason=reason[:500],
            )
        )

    async def add_passage(self, p: Passage) -> None:
        self.s.add(
            PassageRow(
                id=p.id,
                language=p.language,
                title=p.title,
                text=p.text,
                media=p.media,
                source_id=p.source_id,
            )
        )
        await self.s.flush()

    async def get_passage(self, passage_id: UUID) -> Passage | None:
        r = await self.s.get(PassageRow, passage_id)
        return _passage(r) if r else None

    async def list_passages(self, language: str | None, limit: int, offset: int) -> list[Passage]:
        stmt = select(PassageRow).order_by(PassageRow.created_at.desc()).limit(limit).offset(offset)
        if language:
            stmt = stmt.where(PassageRow.language == language)
        return [_passage(r) for r in (await self.s.scalars(stmt)).all()]

    async def save_passage(self, p: Passage) -> None:
        r = await self.s.get(PassageRow, p.id)
        if r is None:
            return
        r.language, r.title, r.text, r.media, r.source_id = (
            p.language,
            p.title,
            p.text,
            p.media,
            p.source_id,
        )
        await self.s.flush()
