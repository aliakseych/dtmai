"""Adapters to other modules. Only their public facades are imported (lazily where the module
is built independently), never their ORM."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank import facade as bank
from app.modules.catalog import facade as catalog
from app.modules.learning import facade as learning
from app.modules.study_plan.domain.exam import ROLE_IQ, CertRule, ExamProfile, ExamSection
from app.modules.study_plan.ports import (
    DailyGrade,
    DailyQuestion,
    DreamTarget,
    MockPoint,
    SubjectInfo,
    WeakSpot,
)
from app.shared.entitlements import entitlements_for

WEAK_LIMIT = 5


def _question(q: bank.QuestionDTO) -> DailyQuestion:
    return DailyQuestion(q.id, q.subject_id, q.kind, q.stem, q.media, q.payload)


class ExamInfoAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def profile(self, direction_code: str) -> ExamProfile | None:
        # Lazy: exam_info is a sibling module; keep import-time coupling out of this one.
        from app.modules.exam_info import facade as exam_info

        p = await exam_info.profile_for_direction(self._s, direction_code)
        if p is None:
            return None
        iq_fallback = next(
            (s.id for s in await catalog.list_subjects(self._s) if s.code == "iq"), None
        )
        sections = tuple(
            ExamSection(
                section_id=s.id,
                role=s.role,
                subject_id=s.subject_id or (iq_fallback if s.role == ROLE_IQ else None),
                max_points=float(s.max_points),
                exemptible=s.exemptible,
                choice_group=s.choice_group,
                subject_options=tuple(p.choices.get(s.choice_group, ())) if s.choice_group else (),
            )
            for s in p.sections
        )
        rules = tuple(
            CertRule(
                r.section_id,
                r.cert_type,
                float(r.min_value) if r.min_value is not None else None,
                float(r.awarded_fraction),
                r.language_subject_id,
                r.active,
            )
            for r in p.rules
        )
        return ExamProfile(
            p.code,
            p.direction_code,
            p.exam_date,
            float(p.max_score),
            p.taper_days,
            p.mock_blueprint_id,
            sections,
            rules,
            p.date_verified,
        )


class LearningAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def mastery(self, user_id: UUID) -> dict[UUID, float | None]:
        stats = await learning.user_stats(self._s, user_id)
        return {s.subject_id: s.mastery for s in stats.by_subject}

    async def weak_spots(self, user_id: UUID, subject_id: UUID) -> list[WeakSpot]:
        areas = await learning.weak_areas(self._s, user_id, subject_id, WEAK_LIMIT)
        return [WeakSpot(a.topic_id, a.type_id) for a in areas]

    async def due_reviews(self, user_id: UUID, subject_id: UUID) -> int:
        return await learning.due_review_count(self._s, user_id, subject_id)

    async def mocks(self, user_id: UUID) -> list[MockPoint]:
        stats = await learning.user_stats(self._s, user_id)
        return [MockPoint(m.taken_at, m.score, m.max_score) for m in stats.mocks]

    async def lesson_queue(self, user_id: UUID, subject_id: UUID, language: str) -> list[UUID]:
        """Not-yet-completed lessons in path order, starting at the placement unit."""
        path = await catalog.get_path(self._s, subject_id, language)
        if path is None:
            return []
        ids = [le.id for u in path.units for le in u.lessons]
        done, start_unit = await learning.path_progress(self._s, user_id, subject_id, ids)
        return [le.id for u in path.units[start_unit:] for le in u.lessons if le.id not in done]

    async def pool(self, subject_id: UUID, language: str) -> int:
        return await bank.count_verified(
            self._s, subject_id=subject_id, topic_ids=None, type_ids=None, language=language
        )


class CatalogAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def subjects(self) -> list[SubjectInfo]:
        return [SubjectInfo(s.id, s.code, s.names) for s in await catalog.list_subjects(self._s)]

    async def mock_minutes(self, blueprint_id: UUID) -> int:
        return (await catalog.get_blueprint(self._s, blueprint_id)).duration_min

    async def mock_servable(self, blueprint_id: UUID, language: str) -> bool:
        """Mirrors assessment.start: a section is empty when it has no fixed questions and
        the verified pool for its filters has nothing to draw."""
        bp = await catalog.get_blueprint(self._s, blueprint_id)
        if not bp.sections:
            return False
        for sec in bp.sections:
            if sec.get("question_ids"):
                continue
            n = await bank.count_verified(
                self._s,
                subject_id=UUID(str(sec["subject_id"])),
                topic_ids=[UUID(str(t)) for t in sec.get("topic_ids") or []] or None,
                type_ids=[UUID(str(t)) for t in sec.get("type_ids") or []] or None,
                language=language,
            )
            if n < 1:
                return False
        return True

    async def topic_names(self, topic_id: UUID) -> dict[str, str]:
        return (await catalog.get_topic(self._s, topic_id)).names


_PICK_ROUNDS = 5


class QuestionAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def pick(
        self, subject_id: UUID, language: str, n: int, exclude: list[UUID]
    ) -> list[DailyQuestion]:
        # Passage groups are not answerable as a single card: exclude them in the query by
        # id (rounds are bounded) so group-heavy subjects still yield single questions.
        picked: list[DailyQuestion] = []
        skipped: list[UUID] = []
        for _ in range(_PICK_ROUNDS):
            qs = await bank.pick_questions(
                self._s,
                subject_id=subject_id,
                language=language,
                n=n * 3,
                exclude_ids=[*exclude, *skipped, *(q.id for q in picked)],
            )
            groups = [q.id for q in qs if q.kind == "passage_group"]
            picked.extend(_question(q) for q in qs if q.kind != "passage_group")
            skipped.extend(groups)
            if len(picked) >= n or not groups:
                break
        return picked[:n]

    async def get(self, ids: list[UUID]) -> list[DailyQuestion]:
        by_id = {q.id: q for q in await bank.get_questions(self._s, ids)}
        return [_question(by_id[i]) for i in ids if i in by_id]

    async def grade(self, question_id: UUID, response: dict[str, Any]) -> DailyGrade:
        g = await bank.grade(self._s, question_id, response)
        return DailyGrade(g.correct, g.correct_response)


class EntitlementAdapter:
    async def has_feature(self, user_id: UUID, feature: str) -> bool:
        return (await entitlements_for(user_id)).has(feature)


class DreamAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def target(self, user_id: UUID) -> DreamTarget | None:
        # Lazy: identity and lyceums are sibling modules built independently.
        from app.modules.identity.wiring import build_identity_service
        from app.modules.lyceums.facade import LyceumBenchmark

        lyceum_id = (await build_identity_service(self._s).get_me(user_id)).target_lyceum_id
        if lyceum_id is None:
            return None
        b = await LyceumBenchmark().benchmark(lyceum_id)
        if b is None:
            return DreamTarget(lyceum_id)
        score = float(b.passing_score) if b.passing_score is not None else None
        ratio = float(b.competition_ratio) if b.competition_ratio is not None else None
        return DreamTarget(lyceum_id, b.year, score, ratio)
