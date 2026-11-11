"""`python -m app seed-exam-info`: insert-only, so admin edits survive every rerun."""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.exam_info.domain.models import FOREIGN_LANGUAGE_GROUP, LYCEUM_MAX_SCORE
from app.modules.exam_info.infrastructure import seed_data as d
from app.modules.exam_info.infrastructure.orm import (
    CertRuleRow,
    ExamEventRow,
    ExamProfileRow,
    FaqRow,
    SectionRow,
    SeededKeyRow,
    SubjectChoiceRow,
)
from app.modules.exam_info.infrastructure.repositories import CatalogSubjectDirectory
from app.modules.exam_info.ports import SubjectDirectory
from app.shared.db import get_engine, get_sessionmaker

log = logging.getLogger(__name__)


async def _first_offer(session: AsyncSession, kind: str, key: str) -> bool:
    """True once per seed key, ever. Admin-deleted events/FAQ are therefore never re-created."""
    res = await session.execute(
        insert(SeededKeyRow)
        .values(kind=kind, key=key)
        .on_conflict_do_nothing()
        .returning(SeededKeyRow.key)
    )
    return res.first() is not None


async def seed(session: AsyncSession, subjects: SubjectDirectory) -> dict[str, int]:
    ids = await subjects.ids_by_code()
    counts = {"profiles": 0, "sections": 0, "rules": 0, "choices": 0, "events": 0, "faq": 0}

    for p in d.profile_specs():
        res = await session.execute(
            insert(ExamProfileRow)
            .values(
                id=p.id,
                code=p.code,
                kind="academic_lyceum",
                direction_code=p.direction_code,
                group_code=p.group_code,
                names=p.names,
                exam_year=d.EXAM_YEAR,
                exam_date=d.EXAM_DATE,
                date_verified=False,
                max_score=LYCEUM_MAX_SCORE,
                taper_days=6,
                source_url=d.SOURCE_URL,
                verified=True,
                active=True,
                position=p.position,
            )
            .on_conflict_do_nothing()
            .returning(ExamProfileRow.id)
        )
        counts["profiles"] += len(res.all())
        for s in p.sections:
            subject_id = ids.get(s.subject_code) if s.subject_code else None
            if s.subject_code and subject_id is None:
                log.warning(
                    "catalog subject %r missing; section %s left unlinked", s.subject_code, s.id
                )
            res = await session.execute(
                insert(SectionRow)
                .values(
                    id=s.id,
                    profile_id=p.id,
                    role=s.role,
                    slot=s.slot,
                    subject_id=subject_id,
                    subject_code=s.subject_code,
                    names=s.names,
                    choice_group=s.choice_group,
                    question_count=s.question_count,
                    points_per_question=s.points_per_question,
                    max_points=s.max_points,
                    exemptible=s.exemptible,
                    position=s.slot,
                )
                .on_conflict_do_nothing()
                .returning(SectionRow.id)
            )
            if res.first() is None:
                # existing section: its rules now belong to the admin; only fill a missing link
                if subject_id is not None:
                    await session.execute(
                        update(SectionRow)
                        .where(SectionRow.id == s.id, SectionRow.subject_id.is_(None))
                        .values(subject_id=subject_id)
                    )
                continue
            counts["sections"] += 1
            counts["rules"] += await _seed_rules(session, s)

    counts["choices"] = await _seed_choices(session, ids)

    for e in d.EVENTS:
        if not await _first_offer(session, "event", f"{d.EXAM_YEAR}:{e.kind}"):
            continue
        res = await session.execute(
            insert(ExamEventRow)
            .values(
                id=d.sid("event", str(d.EXAM_YEAR), e.kind),
                exam_year=d.EXAM_YEAR,
                kind=e.kind,
                starts_on=e.starts_on,
                ends_on=e.ends_on,
                label=e.label,
                verified=False,
                source_url=None,
                position=e.position,
            )
            .on_conflict_do_nothing()
            .returning(ExamEventRow.id)
        )
        counts["events"] += len(res.all())

    for f in d.FAQ:
        if not await _first_offer(session, "faq", f.key):
            continue
        res = await session.execute(
            insert(FaqRow)
            .values(
                id=d.sid("faq", f.key),
                key=f.key,
                category=f.category,
                question=f.question,
                answer=f.answer,
                position=f.position,
                published=True,
                source_url=d.SOURCE_URL if f.verified else None,
                verified=f.verified,
            )
            .on_conflict_do_nothing()
            .returning(FaqRow.id)
        )
        counts["faq"] += len(res.all())
    return counts


async def _seed_rules(session: AsyncSession, s: d.SectionSpec) -> int:
    if s.role != "subject":
        return 0  # IQ is never waived; creative exams are not certificate-based
    certs = d.LANGUAGE_CERTS if s.choice_group == FOREIGN_LANGUAGE_GROUP else (d.SUBJECT_CERT,)
    for c in certs:
        await session.execute(
            insert(CertRuleRow)
            .values(
                id=d.sid("rule", str(s.id), c.cert_type),
                section_id=s.id,
                cert_type=c.cert_type,
                level_label=c.level_label,
                min_value=c.min_value,
                awarded_fraction=1,
                note=c.note if any(c.note.values()) else {},
                verified=c.verified,
                source_url=d.SOURCE_URL,
                active=c.active,
            )
            .on_conflict_do_nothing()
        )
    return len(certs)


async def _seed_choices(session: AsyncSession, ids: dict[str, UUID]) -> int:
    n = 0
    for pos, code in enumerate(d.FOREIGN_LANGUAGE_CODES):
        if code not in ids:
            log.warning("catalog subject %r missing; not offered as a foreign language", code)
            continue
        res = await session.execute(
            insert(SubjectChoiceRow)
            .values(choice_group=FOREIGN_LANGUAGE_GROUP, subject_id=ids[code], position=pos)
            .on_conflict_do_nothing()
            .returning(SubjectChoiceRow.subject_id)
        )
        n += len(res.all())
    return n


async def _run() -> None:
    async with get_sessionmaker()() as session:
        counts = await seed(session, CatalogSubjectDirectory(session))
        await session.commit()
    # Pooled connections are bound to this event loop; other CLI seeds run their own loop.
    await get_engine().dispose()
    print("seeded exam_info:", counts)


def main() -> int:
    asyncio.run(_run())
    return 0
