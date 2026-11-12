"""Public facade of the bank module. Other modules import ONLY this file."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank.application.service import BankService, CreateQuestionCmd
from app.modules.bank.domain.models import Passage, Question
from app.modules.bank.infrastructure.repositories import SqlQuestionRepository
from app.modules.bank.settings import get_bank_settings

__all__ = [
    "CreateQuestionCmd",
    "GradeResult",
    "QuestionDTO",
    "content_min_pool",
    "count_verified",
    "FacetRow",
    "count_verified_by_source",
    "facets",
    "create_passage",
    "create_question",
    "AnswerInfo",
    "get_answer",
    "get_answer_info",
    "get_passage",
    "get_explanation",
    "get_questions",
    "grade",
    "pick_questions",
    "set_answer",
    "set_status",
    "upsert_explanation",
]


@dataclass(frozen=True, slots=True)
class QuestionDTO:
    id: UUID
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    difficulty: float
    stem: str  # markdown + KaTeX
    media: list[Any]
    payload: dict[str, Any]  # kind-specific; never contains the answer
    passage_id: UUID | None
    source_id: UUID | None
    status: str
    parent_id: UUID | None = None
    options_generated: bool = False  # distractors were AI-made at ingestion; needs human review
    children: list["QuestionDTO"] = field(default_factory=list)  # filled for passage_group


@dataclass(frozen=True, slots=True)
class GradeResult:
    correct: bool
    score: float
    correct_response: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AnswerInfo:
    response: dict[str, Any]
    official: bool


def service(session: AsyncSession) -> BankService:
    return BankService(
        SqlQuestionRepository(session),
        report_hide_threshold=get_bank_settings().question_report_hide_threshold,
    )


def to_dto(q: Question) -> QuestionDTO:
    return QuestionDTO(
        id=q.id,
        subject_id=q.subject_id,
        topic_id=q.topic_id,
        type_id=q.type_id,
        kind=q.kind,
        language=q.language,
        difficulty=q.difficulty,
        stem=q.stem,
        media=list(q.media),
        payload=dict(q.payload),
        passage_id=q.passage_id,
        source_id=q.source_id,
        status=q.status,
        parent_id=q.parent_id,
        options_generated=bool((q.source_ref or {}).get("options_generated")),
    )


async def _with_children(svc: BankService, qs: list[Question]) -> list[QuestionDTO]:
    child_ids = [
        UUID(c) for q in qs if q.kind == "passage_group" for c in q.payload.get("child_ids", [])
    ]
    kids = {k.id: k for k in await svc.get_many(child_ids)}
    out: list[QuestionDTO] = []
    for q in qs:
        dto = to_dto(q)
        if q.kind == "passage_group":
            dto.children.extend(
                to_dto(kids[UUID(c)]) for c in q.payload.get("child_ids", []) if UUID(c) in kids
            )
        out.append(dto)
    return out


async def get_questions(session: AsyncSession, ids: Sequence[UUID]) -> list[QuestionDTO]:
    svc = service(session)
    return await _with_children(svc, await svc.get_many(list(ids)))


async def pick_questions(
    session: AsyncSession,
    *,
    subject_id: UUID,
    topic_ids: Sequence[UUID] | None = None,
    type_ids: Sequence[UUID] | None = None,
    language: str,
    n: int,
    exclude_ids: Sequence[UUID] = (),
    difficulty: float | None = None,
    statuses: Sequence[str] = ("verified",),
    source_id: UUID | None = None,
    level: str | None = None,
) -> list[QuestionDTO]:
    """Random pick (nearest to `difficulty` Elo first when given). Group children are served
    inside their passage_group question's `children`."""
    svc = service(session)
    qs = await svc.pick(
        subject_id=subject_id,
        topic_ids=topic_ids,
        type_ids=type_ids,
        language=language,
        n=n,
        exclude_ids=exclude_ids,
        difficulty=difficulty,
        statuses=statuses,
        source_id=source_id,
        level=level,
    )
    return await _with_children(svc, qs)


@dataclass(frozen=True, slots=True)
class FacetRow:
    topic_id: UUID
    type_id: UUID
    source_id: UUID | None
    level: str  # easy | medium | hard
    total: int
    solved: int


async def facets(
    session: AsyncSession, subject_id: UUID, language: str, solved_ids: Sequence[UUID]
) -> list[FacetRow]:
    """Learner-servable (verified) question counts of a subject/language by topic, type, source
    and difficulty level, with how many of them are in `solved_ids`."""
    rows = await service(session).repo.facets(subject_id, language, solved_ids)
    return [FacetRow(*r) for r in rows]


async def grade(session: AsyncSession, question_id: UUID, response: dict[str, Any]) -> GradeResult:
    out = await service(session).grade(question_id, response)
    return GradeResult(out.correct, out.score, out.correct_response)


async def create_question(session: AsyncSession, cmd: CreateQuestionCmd) -> UUID:
    return await service(session).create(cmd)


async def set_status(
    session: AsyncSession, question_id: UUID, status: str, actor: Any, reason: str = ""
) -> None:
    await service(session).set_status(question_id, status, actor, reason)


async def upsert_explanation(
    session: AsyncSession, question_id: UUID, locale: str, text: str, model: str
) -> None:
    await service(session).upsert_explanation(question_id, locale, text, model)


async def get_explanation(session: AsyncSession, question_id: UUID, locale: str) -> str | None:
    return await service(session).get_explanation(question_id, locale)


async def set_answer(
    session: AsyncSession,
    question_id: UUID,
    response: dict[str, Any],
    actor: Any,
    *,
    official: bool = False,
) -> None:
    await service(session).set_answer(question_id, response, actor, official=official)


async def get_answer(session: AsyncSession, question_id: UUID) -> dict[str, Any]:
    """Hidden answer; for labeling/admin only, never for learner responses."""
    return await service(session).get_answer(question_id)


async def get_answer_info(session: AsyncSession, question_id: UUID) -> AnswerInfo:
    svc = service(session)
    q = await svc.require(question_id)
    return AnswerInfo(await svc.get_answer(question_id), q.answer_official)


async def get_passage(session: AsyncSession, passage_id: UUID) -> Passage | None:
    """Passage with .id/.language/.title/.text/.media/.source_id, or None."""
    return await SqlQuestionRepository(session).get_passage(passage_id)


async def create_passage(
    session: AsyncSession,
    *,
    language: str,
    text: str,
    title: str | None = None,
    media: list[Any] | None = None,
    source_id: UUID | None = None,
) -> UUID:
    return await service(session).create_passage(
        language=language, text=text, title=title, media=media, source_id=source_id
    )


async def count_verified(
    session: AsyncSession,
    *,
    subject_id: UUID,
    topic_ids: Sequence[UUID] | None,
    type_ids: Sequence[UUID] | None,
    language: str,
) -> int:
    return await service(session).count_verified(subject_id, topic_ids, type_ids, language)


async def count_verified_by_source(session: AsyncSession, source_id: UUID) -> int:
    """Verified, learner-servable questions that belong to one question base."""
    from app.modules.bank.domain.models import QuestionFilter

    _, total = await service(session).search(
        QuestionFilter(source_id=source_id, status="verified"), 1, 0
    )
    return total


async def count_verified_for_subject(session: AsyncSession, subject_id: UUID) -> int:
    """Verified, learner-servable questions of one subject (any language)."""
    from app.modules.bank.domain.models import QuestionFilter

    _, total = await service(session).search(
        QuestionFilter(subject_id=subject_id, status="verified", learner_visible=True), 1, 0
    )
    return total


def content_min_pool() -> int:
    return get_bank_settings().content_min_pool
