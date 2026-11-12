from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog import facade as catalog_facade
from app.modules.exam_info.domain.models import (
    CertRule,
    DuplicateKey,
    ExamEvent,
    ExamProfile,
    FaqItem,
    Section,
)
from app.modules.exam_info.infrastructure.orm import (
    CertRuleRow,
    ExamEventRow,
    ExamProfileRow,
    FaqRow,
    SectionRow,
    SubjectChoiceRow,
)


def _section(r: SectionRow) -> Section:
    return Section(
        id=r.id,
        role=r.role,
        slot=r.slot,
        names=r.names,
        subject_id=r.subject_id,
        subject_code=r.subject_code,
        choice_group=r.choice_group,
        question_count=r.question_count,
        points_per_question=r.points_per_question,
        max_points=r.max_points,
        exemptible=r.exemptible,
        position=r.position,
    )


def _rule(r: CertRuleRow) -> CertRule:
    return CertRule(
        id=r.id,
        section_id=r.section_id,
        cert_type=r.cert_type,
        language_subject_id=r.language_subject_id,
        level_label=r.level_label,
        min_value=r.min_value,
        awarded_fraction=r.awarded_fraction,
        note=r.note,
        verified=r.verified,
        source_url=r.source_url,
        active=r.active,
    )


def _event(r: ExamEventRow) -> ExamEvent:
    return ExamEvent(
        id=r.id,
        exam_year=r.exam_year,
        kind=r.kind,
        starts_on=r.starts_on,
        ends_on=r.ends_on,
        label=r.label,
        verified=r.verified,
        source_url=r.source_url,
        position=r.position,
    )


def _faq(r: FaqRow) -> FaqItem:
    return FaqItem(
        id=r.id,
        key=r.key,
        category=r.category,
        question=r.question,
        answer=r.answer,
        position=r.position,
        published=r.published,
        source_url=r.source_url,
        verified=r.verified,
        updated_at=r.updated_at,
        updated_by=r.updated_by,
    )


class SqlExamInfoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _assemble(self, rows: list[ExamProfileRow]) -> list[ExamProfile]:
        if not rows:
            return []
        ids = [r.id for r in rows]
        sections = (
            await self._s.scalars(
                select(SectionRow).where(SectionRow.profile_id.in_(ids)).order_by(SectionRow.slot)
            )
        ).all()
        sec_ids = [s.id for s in sections]
        rules = (
            (
                await self._s.scalars(
                    select(CertRuleRow).where(CertRuleRow.section_id.in_(sec_ids))
                )
            ).all()
            if sec_ids
            else []
        )
        choice_rows = (
            await self._s.scalars(
                select(SubjectChoiceRow).order_by(
                    SubjectChoiceRow.choice_group, SubjectChoiceRow.position
                )
            )
        ).all()
        choices: dict[str, list[UUID]] = defaultdict(list)
        for c in choice_rows:
            choices[c.choice_group].append(c.subject_id)
        by_profile: dict[UUID, list[SectionRow]] = defaultdict(list)
        for s in sections:
            by_profile[s.profile_id].append(s)
        rules_by_profile: dict[UUID, list[CertRule]] = defaultdict(list)
        owner = {s.id: s.profile_id for s in sections}
        for r in rules:
            rules_by_profile[owner[r.section_id]].append(_rule(r))
        return [
            ExamProfile(
                id=p.id,
                code=p.code,
                kind=p.kind,
                names=p.names,
                exam_year=p.exam_year,
                max_score=p.max_score,
                direction_code=p.direction_code,
                group_code=p.group_code,
                exam_date=p.exam_date,
                date_verified=p.date_verified,
                trust_self_declared=p.trust_self_declared,
                taper_days=p.taper_days,
                mock_blueprint_id=p.mock_blueprint_id,
                source_url=p.source_url,
                verified=p.verified,
                active=p.active,
                position=p.position,
                sections=tuple(_section(s) for s in by_profile[p.id]),
                rules=tuple(rules_by_profile[p.id]),
                choices={g: tuple(v) for g, v in choices.items()},
            )
            for p in rows
        ]

    async def list_profiles(self, *, active_only: bool) -> list[ExamProfile]:
        stmt = select(ExamProfileRow).order_by(
            ExamProfileRow.exam_year.desc(), ExamProfileRow.position, ExamProfileRow.code
        )
        if active_only:
            stmt = stmt.where(ExamProfileRow.active.is_(True))
        return await self._assemble(list((await self._s.scalars(stmt)).all()))

    async def get_profile(self, profile_id: UUID) -> ExamProfile | None:
        row = await self._s.get(ExamProfileRow, profile_id)
        return (await self._assemble([row]))[0] if row else None

    async def get_profile_by_direction(
        self, direction_code: str, *, active_only: bool
    ) -> ExamProfile | None:
        stmt = (
            select(ExamProfileRow)
            .where(ExamProfileRow.direction_code == direction_code)
            .order_by(ExamProfileRow.exam_year.desc())
            .limit(1)
        )
        if active_only:
            stmt = stmt.where(ExamProfileRow.active.is_(True))
        row = await self._s.scalar(stmt)
        return (await self._assemble([row]))[0] if row else None

    async def update_profile(self, profile_id: UUID, fields: dict[str, Any]) -> None:
        if fields:
            await self._s.execute(
                update(ExamProfileRow).where(ExamProfileRow.id == profile_id).values(**fields)
            )

    async def get_section(self, section_id: UUID) -> Section | None:
        row = await self._s.get(SectionRow, section_id)
        return _section(row) if row else None

    async def set_section_subject(self, section_id: UUID, subject_id: UUID | None) -> None:
        code: str | None = None
        if subject_id is not None:
            subjects = await catalog_facade.list_subjects(self._s, active_only=False)
            code = next((s.code for s in subjects if s.id == subject_id), None)
        await self._s.execute(
            update(SectionRow)
            .where(SectionRow.id == section_id)
            .values(subject_id=subject_id, subject_code=code)
        )

    async def replace_choice(self, group: str, subject_ids: list[UUID]) -> None:
        await self._s.execute(
            delete(SubjectChoiceRow).where(SubjectChoiceRow.choice_group == group)
        )
        self._s.add_all(
            SubjectChoiceRow(choice_group=group, subject_id=sid, position=i)
            for i, sid in enumerate(dict.fromkeys(subject_ids))
        )
        await self._s.flush()

    async def get_rule(self, rule_id: UUID) -> CertRule | None:
        row = await self._s.get(CertRuleRow, rule_id)
        return _rule(row) if row else None

    async def _upsert(self, model: type[Any], pk: UUID, values: dict[str, Any]) -> None:
        """Insert or update by primary key; a unique-key clash becomes `DuplicateKey`."""
        try:
            async with self._s.begin_nested():
                row = await self._s.get(model, pk)
                if row is None:
                    self._s.add(model(id=pk, **values))
                else:
                    for k, v in values.items():
                        setattr(row, k, v)
                await self._s.flush()
        except IntegrityError as exc:
            raise DuplicateKey("an entry with the same key already exists") from exc

    async def save_rule(self, rule: CertRule) -> None:
        await self._upsert(
            CertRuleRow,
            rule.id,
            {
                "section_id": rule.section_id,
                "cert_type": rule.cert_type,
                "language_subject_id": rule.language_subject_id,
                "level_label": rule.level_label,
                "min_value": rule.min_value,
                "awarded_fraction": rule.awarded_fraction,
                "note": rule.note,
                "verified": rule.verified,
                "source_url": rule.source_url,
                "active": rule.active,
            },
        )

    async def delete_rule(self, rule_id: UUID) -> bool:
        res = await self._s.execute(delete(CertRuleRow).where(CertRuleRow.id == rule_id))
        return bool(res.rowcount)  # type: ignore[attr-defined]

    async def list_events(self, exam_year: int | None) -> list[ExamEvent]:
        stmt = select(ExamEventRow).order_by(ExamEventRow.exam_year, ExamEventRow.position)
        if exam_year is not None:
            stmt = stmt.where(ExamEventRow.exam_year == exam_year)
        return [_event(r) for r in (await self._s.scalars(stmt)).all()]

    async def get_event(self, event_id: UUID) -> ExamEvent | None:
        row = await self._s.get(ExamEventRow, event_id)
        return _event(row) if row else None

    async def save_event(self, event: ExamEvent) -> None:
        await self._upsert(
            ExamEventRow,
            event.id,
            {
                "exam_year": event.exam_year,
                "kind": event.kind,
                "starts_on": event.starts_on,
                "ends_on": event.ends_on,
                "label": event.label,
                "verified": event.verified,
                "source_url": event.source_url,
                "position": event.position,
            },
        )

    async def delete_event(self, event_id: UUID) -> bool:
        res = await self._s.execute(delete(ExamEventRow).where(ExamEventRow.id == event_id))
        return bool(res.rowcount)  # type: ignore[attr-defined]

    async def list_faq(self, *, published_only: bool, category: str | None) -> list[FaqItem]:
        stmt = select(FaqRow).order_by(FaqRow.category, FaqRow.position, FaqRow.key)
        if published_only:
            stmt = stmt.where(FaqRow.published.is_(True))
        if category:
            stmt = stmt.where(FaqRow.category == category)
        return [_faq(r) for r in (await self._s.scalars(stmt)).all()]

    async def get_faq(self, faq_id: UUID) -> FaqItem | None:
        row = await self._s.get(FaqRow, faq_id)
        return _faq(row) if row else None

    async def save_faq(self, item: FaqItem) -> None:
        await self._upsert(
            FaqRow,
            item.id,
            {
                "key": item.key,
                "category": item.category,
                "question": item.question,
                "answer": item.answer,
                "position": item.position,
                "published": item.published,
                "source_url": item.source_url,
                "verified": item.verified,
                "updated_by": item.updated_by,
            },
        )

    async def delete_faq(self, faq_id: UUID) -> bool:
        res = await self._s.execute(delete(FaqRow).where(FaqRow.id == faq_id))
        return bool(res.rowcount)  # type: ignore[attr-defined]


class CatalogSubjectDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def ids_by_code(self) -> dict[str, UUID]:
        return {
            s.code: s.id for s in await catalog_facade.list_subjects(self._s, active_only=False)
        }
