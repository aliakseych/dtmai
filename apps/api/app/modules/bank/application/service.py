import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.modules.bank.domain.kinds import (
    InvalidQuestion,
    check_text_quality,
    empirical_difficulty,
    grade_group,
    grade_response,
    is_group,
    validate_question,
)
from app.modules.bank.domain.models import (
    DEFAULT_DIFFICULTY,
    STATUSES,
    Passage,
    Question,
    QuestionFilter,
    transition_allowed,
)
from app.modules.bank.ports import QuestionRepository
from app.shared.errors import Conflict, NotFound, ValidationFailed
from app.shared.ids import new_id

_LANG = re.compile(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")
_PATCHABLE = {
    "stem",
    "payload",
    "answer",
    "topic_id",
    "type_id",
    "difficulty",
    "media",
    "passage_id",
    "source_id",
    "source_ref",
    "translation_group_id",
    "language",
}


@dataclass(slots=True)
class CreateQuestionCmd:
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    stem: str
    payload: dict[str, Any]
    answer: dict[str, Any]
    difficulty: float = DEFAULT_DIFFICULTY
    media: list[Any] = field(default_factory=list)
    passage_id: UUID | None = None
    source_id: UUID | None = None
    source_ref: dict[str, Any] | None = None
    status: str = "draft"
    answer_official: bool = False
    translation_group_id: UUID | None = None
    children: list["CreateQuestionCmd"] = field(default_factory=list)
    created_by: str | None = None


@dataclass(frozen=True, slots=True)
class GradeOutcome:
    correct: bool
    score: float
    correct_response: dict[str, Any]


@dataclass(slots=True)
class ImportResult:
    created: list[UUID] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)


def _json(v: Any) -> Any:
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _json(x) for k, x in v.items()}
    if isinstance(v, list | tuple):
        return [_json(x) for x in v]
    return v


def question_json(q: Question) -> dict[str, Any]:
    return _json(asdict(q))


def _actor(actor: Any) -> str | None:
    return None if actor is None else str(actor)


class BankService:
    def __init__(self, repo: QuestionRepository, *, report_hide_threshold: int = 3) -> None:
        self.repo = repo
        self.report_hide_threshold = report_hide_threshold

    # ---- reads -------------------------------------------------------------------------
    async def get_many(self, ids: Sequence[UUID]) -> list[Question]:
        return await self.repo.get_many(ids)

    async def require(self, qid: UUID) -> Question:
        found = await self.repo.get_many([qid])
        if not found:
            raise NotFound("question not found", code="question_not_found")
        return found[0]

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
    ) -> list[Question]:
        return await self.repo.pick(
            subject_id=subject_id,
            topic_ids=topic_ids,
            type_ids=type_ids,
            language=language,
            n=n,
            exclude_ids=exclude_ids,
            difficulty=difficulty,
            statuses=statuses,
        )

    async def count_verified(
        self,
        subject_id: UUID,
        topic_ids: Sequence[UUID] | None,
        type_ids: Sequence[UUID] | None,
        language: str,
    ) -> int:
        return await self.repo.count(
            subject_id=subject_id,
            topic_ids=topic_ids,
            type_ids=type_ids,
            language=language,
            statuses=("verified",),
        )

    async def search(
        self, f: QuestionFilter, limit: int, offset: int
    ) -> tuple[list[Question], int]:
        return await self.repo.search(f, limit, offset)

    async def coverage(
        self, subject_id: UUID | None, language: str | None
    ) -> list[tuple[UUID, UUID, UUID, str, int]]:
        return await self.repo.coverage(subject_id, language)

    # ---- grading -----------------------------------------------------------------------
    async def grade(self, qid: UUID, response: Mapping[str, Any]) -> GradeOutcome:
        q = await self.require(qid)
        if is_group(q.kind):
            return await self._grade_group(q, response)
        g = grade_response(q.kind, q.payload, q.answer, response)
        return GradeOutcome(g.correct, g.score, dict(q.answer))

    async def _grade_group(self, q: Question, response: Mapping[str, Any]) -> GradeOutcome:
        children = await self.repo.get_many([UUID(c) for c in q.payload.get("child_ids", [])])
        g, correct_response = grade_group(
            [(str(c.id), c.kind, c.payload, c.answer) for c in children], response
        )
        return GradeOutcome(g.correct, g.score, correct_response)

    async def get_answer(self, qid: UUID) -> dict[str, Any]:
        q = await self.require(qid)
        if is_group(q.kind):
            kids = await self.repo.get_many([UUID(c) for c in q.payload.get("child_ids", [])])
            return {"answers": {str(c.id): dict(c.answer) for c in kids}}
        return dict(q.answer)

    # ---- writes ------------------------------------------------------------------------
    async def create(self, cmd: CreateQuestionCmd) -> UUID:
        if cmd.status not in STATUSES:
            raise ValidationFailed(f"unknown status {cmd.status!r}", code="invalid_status")
        if not _LANG.match(cmd.language):
            raise ValidationFailed("invalid content language", code="invalid_language")
        if not cmd.stem.strip():
            raise ValidationFailed("stem is required", code="invalid_question")
        payload = dict(cmd.payload)
        qid = new_id()
        if is_group(cmd.kind):
            if not cmd.children:
                raise ValidationFailed("passage_group needs children", code="invalid_question")
            child_ids: list[UUID] = []
            for child in cmd.children:
                if is_group(child.kind):
                    raise ValidationFailed("groups cannot be nested", code="invalid_question")
                child.passage_id = child.passage_id or cmd.passage_id
                child_ids.append(await self._insert(child, parent_id=qid))
            payload["child_ids"] = [str(c) for c in child_ids]
        self._validate(cmd.kind, payload, cmd.answer, cmd.stem)
        q = self._build(qid, cmd, payload, None)
        await self.repo.add(q)
        await self.repo.add_audit(cmd.created_by, "create", qid, None, question_json(q))
        return qid

    async def _insert(self, cmd: CreateQuestionCmd, *, parent_id: UUID) -> UUID:
        self._validate(cmd.kind, cmd.payload, cmd.answer, cmd.stem)
        qid = new_id()
        q = self._build(qid, cmd, dict(cmd.payload), parent_id)
        await self.repo.add(q)
        return qid

    @staticmethod
    def _build(
        qid: UUID, cmd: CreateQuestionCmd, payload: dict[str, Any], parent_id: UUID | None
    ) -> Question:
        return Question(
            id=qid,
            subject_id=cmd.subject_id,
            topic_id=cmd.topic_id,
            type_id=cmd.type_id,
            kind=cmd.kind,
            language=cmd.language,
            stem=cmd.stem,
            payload=payload,
            answer=dict(cmd.answer),
            difficulty=cmd.difficulty,
            media=list(cmd.media),
            passage_id=cmd.passage_id,
            parent_id=parent_id,
            source_id=cmd.source_id,
            source_ref=cmd.source_ref,
            translation_group_id=cmd.translation_group_id,
            status=cmd.status,
            answer_official=cmd.answer_official,
            created_by=cmd.created_by,
        )

    @staticmethod
    def _validate(
        kind: str, payload: Mapping[str, Any], answer: Mapping[str, Any], stem: str = ""
    ) -> None:
        try:
            validate_question(kind, payload, answer)
            check_text_quality(stem, payload)
        except InvalidQuestion as e:
            raise ValidationFailed(str(e), code="invalid_question") from e

    async def update(self, qid: UUID, patch: Mapping[str, Any], actor: Any) -> Question:
        q = await self.require(qid)
        before = question_json(q)
        for k, v in patch.items():
            if k not in _PATCHABLE:
                raise ValidationFailed(f"field {k!r} is not editable", code="invalid_field")
            setattr(q, k, v)
        if not _LANG.match(q.language) or not q.stem.strip():
            raise ValidationFailed("invalid language or empty stem", code="invalid_question")
        if is_group(q.kind):
            # a group's answer lives in its children
            self._validate(q.kind, q.payload, {}, q.stem)
        else:
            self._validate(q.kind, q.payload, q.answer, q.stem)
        if "answer" in patch and q.answer_official:
            q.answer_official = False  # an edited answer is no longer the official key
        await self.repo.save(q)
        await self.repo.add_audit(_actor(actor), "update", qid, before, question_json(q))
        return q

    async def set_status(self, qid: UUID, status: str, actor: Any, reason: str = "") -> None:
        if status not in STATUSES:
            raise ValidationFailed(f"unknown status {status!r}", code="invalid_status")
        q = await self.require(qid)
        if not transition_allowed(q.status, status):
            raise Conflict(f"cannot move {q.status} -> {status}", code="invalid_transition")
        if status == "verified":
            self._validate(q.kind, q.payload, {} if is_group(q.kind) else q.answer, q.stem)
        before = q.status
        q.status = status
        await self.repo.save(q)
        if is_group(q.kind):
            await self.repo.bulk_set_status(
                [UUID(c) for c in q.payload.get("child_ids", [])], status
            )
        await self.repo.add_audit(
            _actor(actor), "set_status", qid, {"status": before}, {"status": status}, reason
        )

    async def bulk_set_status(
        self, ids: Sequence[UUID], status: str, actor: Any, reason: str = ""
    ) -> int:
        done = 0
        for qid in dict.fromkeys(ids):
            try:
                await self.set_status(qid, status, actor, reason)
                done += 1
            except (NotFound, Conflict, ValidationFailed):
                continue
        return done

    async def set_answer(
        self, qid: UUID, response: dict[str, Any], actor: Any, *, official: bool
    ) -> None:
        q = await self.require(qid)
        if is_group(q.kind):
            raise ValidationFailed("set answers on the group's children", code="invalid_question")
        if q.answer_official and not official:
            raise Conflict("official answer cannot be overwritten", code="answer_official")
        self._validate(q.kind, q.payload, response, q.stem)
        before = dict(q.answer)
        q.answer = dict(response)
        q.answer_official = official or q.answer_official
        await self.repo.save(q)
        await self.repo.add_audit(
            _actor(actor),
            "set_answer",
            qid,
            {"answer": before},
            {"answer": response, "official": official},
        )

    async def upsert_explanation(self, qid: UUID, locale: str, text: str, model: str) -> None:
        await self.require(qid)
        await self.repo.upsert_explanation(qid, locale, text, model)

    async def get_explanation(self, qid: UUID, locale: str) -> str | None:
        return await self.repo.get_explanation(qid, locale)

    async def import_items(self, items: Sequence[Mapping[str, Any]], actor: Any) -> ImportResult:
        res = ImportResult()
        for i, raw in enumerate(items):
            try:
                res.created.append(await self.create(_cmd_from_dict(raw, _actor(actor))))
            except (ValidationFailed, KeyError, ValueError, TypeError) as e:
                res.errors.append((i, str(e) or type(e).__name__))
        return res

    async def report(self, qid: UUID, user_id: UUID, reason: str) -> bool:
        """Records a learner report; returns True when the question was auto-hidden."""
        q = await self.require(qid)
        n = await self.repo.add_report(qid, user_id, reason)
        if q.status == "verified" and n >= self.report_hide_threshold:
            await self.set_status(qid, "hidden", None, f"auto-hidden after {n} reports")
            return True
        return False

    # ---- passages ----------------------------------------------------------------------
    async def create_passage(
        self,
        *,
        language: str,
        text: str,
        title: str | None,
        media: list[Any] | None,
        source_id: UUID | None,
    ) -> UUID:
        if not _LANG.match(language) or not text.strip():
            raise ValidationFailed("passage needs language and text", code="invalid_passage")
        pid = uuid4()
        await self.repo.add_passage(Passage(pid, language, text, title, media or [], source_id))
        return pid

    async def update_passage(self, pid: UUID, patch: Mapping[str, Any]) -> Passage:
        p = await self.repo.get_passage(pid)
        if p is None:
            raise NotFound("passage not found", code="passage_not_found")
        for k, v in patch.items():
            if k in ("language", "text", "title", "media", "source_id"):
                setattr(p, k, v)
        await self.repo.save_passage(p)
        return p

    # ---- events ------------------------------------------------------------------------
    async def apply_attempt(self, event_id: UUID, question_id: UUID, correct: bool) -> None:
        """Idempotent on event id. Refreshes the empirical Elo-scale difficulty."""
        if not await self.repo.claim_event(event_id):
            return
        await self.repo.record_attempt(question_id, correct)
        found = await self.repo.get_many([question_id])
        if found:
            q = found[0]
            new = empirical_difficulty(q.attempts, q.correct_count)
            if new is not None and new != q.difficulty:
                q.difficulty = new
                await self.repo.save(q)


def _cmd_from_dict(raw: Mapping[str, Any], actor: str | None) -> CreateQuestionCmd:
    def one(d: Mapping[str, Any]) -> CreateQuestionCmd:
        uid = lambda k: UUID(str(d[k])) if d.get(k) else None  # noqa: E731
        return CreateQuestionCmd(
            subject_id=UUID(str(d["subject_id"])),
            topic_id=UUID(str(d["topic_id"])),
            type_id=UUID(str(d["type_id"])),
            kind=d["kind"],
            language=d["language"],
            stem=d["stem"],
            payload=dict(d.get("payload") or {}),
            answer=dict(d.get("answer") or {}),
            difficulty=float(d.get("difficulty", DEFAULT_DIFFICULTY)),
            media=list(d.get("media") or []),
            passage_id=uid("passage_id"),
            source_id=uid("source_id"),
            source_ref=d.get("source_ref"),
            status=d.get("status", "draft"),
            answer_official=bool(d.get("answer_official", False)),
            translation_group_id=uid("translation_group_id"),
            children=[one(c) for c in d.get("children") or []],
            created_by=actor,
        )

    return one(raw)
