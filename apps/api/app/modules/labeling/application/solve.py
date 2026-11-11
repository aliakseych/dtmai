import asyncio
import logging
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.application.errors import AIBudgetExhausted
from app.modules.ai.application.gateway import AIGateway
from app.modules.ai.domain.routing import ModelRoute, Task
from app.modules.bank import facade as bank
from app.modules.labeling.application import prompts
from app.modules.labeling.domain.agreement import (
    Decision,
    SolverVote,
    Status,
    evaluate_escalation,
    evaluate_solve,
)
from app.modules.labeling.domain.answers import FREE_FORM_KINDS, SOLVABLE_KINDS, canonical
from app.modules.labeling.infrastructure.orm import QueueItemRow, SolveRunRow, SolverVoteRow
from app.shared.errors import DomainError
from app.shared.ids import new_id

log = logging.getLogger(__name__)

MACHINE_ACTOR = "labeling:auto"
PROTECTED_STATUSES = frozenset({"verified", "hidden", "retired"})


@dataclass(frozen=True, slots=True)
class SolveOutcome:
    question_id: UUID
    run_id: UUID | None
    status: str | None  # None when skipped
    reason: str
    confidence: float = 0.0


def _vote_from_json(model: str, data: dict[str, Any]) -> SolverVote:
    answer = data.get("answer")
    try:
        conf = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    if not isinstance(answer, dict):
        return SolverVote(model, None, 0.0, ok=False)
    return SolverVote(model, answer, max(0.0, min(1.0, conf)), ok=True)


class SolveService:
    def __init__(
        self, session: AsyncSession, gateway: AIGateway, *, min_models: int = 2, min_confidence: float = 0.7
    ) -> None:
        self._s = session
        self._gw = gateway
        self._min_models = min_models
        self._min_conf = min_confidence

    async def solve_question(self, question_id: UUID, *, trigger: str) -> SolveOutcome:
        (q,) = await bank.get_questions(self._s, [question_id]) or (None,)
        if q is None:
            return SolveOutcome(question_id, None, "not_found")
        if q.kind not in SOLVABLE_KINDS:
            return SolveOutcome(question_id, None, "unsupported_kind")
        info = await bank.get_answer_info(self._s, question_id)
        official = info.response if info.official else None
        passage = None
        if q.passage_id is not None:
            p = await bank.get_passage(self._s, q.passage_id)
            passage = p.text if p is not None else None

        routes = await self._gw.routes(Task.SOLVE)
        votes_raw = await asyncio.gather(
            *(self._solve_once(r, q.kind, q.stem, q.payload, passage, question_id) for r in routes)
        )
        votes: list[SolverVote] = []
        for v in votes_raw:
            if isinstance(v, AIBudgetExhausted):
                raise v
            votes.append(v)
        stages: list[tuple[str, SolverVote]] = [("solve", v) for v in votes]

        if q.kind in FREE_FORM_KINDS and official is None:
            votes = await self._merge_equivalent(q.kind, q.stem, votes, question_id)

        decision = evaluate_solve(
            q.kind, votes, official_key=official, min_models=self._min_models, min_confidence=self._min_conf
        )
        if (
            trigger == "generation"
            and official is None
            and decision.status is Status.AUTO_AGREED
            and decision.response is not None
            and canonical(q.kind, decision.response) != canonical(q.kind, info.response)
        ):
            decision = Decision(Status.ESCALATED, decision.response, decision.confidence * 0.5, "stored_mismatch")

        if decision.status is Status.ESCALATED:
            adj = await self._adjudicate(q.kind, q.stem, q.payload, passage, votes, question_id)
            if adj is not None:
                stages.append(("adjudicate", adj))
            decision = evaluate_escalation(q.kind, decision, adj)

        run_id = await self._persist(question_id, trigger, decision, stages)
        await self._apply(q, info.response, decision, run_id)
        return SolveOutcome(question_id, run_id, decision.status.value, decision.reason, decision.confidence)

    # -- model calls ------------------------------------------------------------------
    async def _solve_once(
        self, route: ModelRoute, kind: str, stem: str, payload: dict[str, Any], passage: str | None, qid: UUID
    ) -> SolverVote | AIBudgetExhausted:
        try:
            data, _ = await self._gw.complete_json(
                route, prompts.solve_messages(kind, stem, payload, passage), purpose="labeling.solve", ref=str(qid)
            )
        except AIBudgetExhausted as e:
            return e
        except DomainError as e:
            log.warning("solver %s failed for %s: %s", route.model, qid, e.detail)
            return SolverVote(route.model, None, 0.0, ok=False)
        return _vote_from_json(route.model, data)  # type: ignore[arg-type]

    async def _judge_route(self, slot: int) -> ModelRoute | None:
        try:
            return next((r for r in await self._gw.routes(Task.JUDGE) if r.slot == slot), None)
        except DomainError:
            return None

    async def _merge_equivalent(
        self, kind: str, stem: str, votes: list[SolverVote], qid: UUID
    ) -> list[SolverVote]:
        valid = [v for v in votes if v.ok and v.response is not None and canonical(kind, v.response)]
        distinct: dict[str, SolverVote] = {}
        for v in valid:
            distinct.setdefault(canonical(kind, v.response or {}) or "", v)
        if len(distinct) < 2:
            return votes
        route = await self._judge_route(0)
        if route is None:
            return votes
        reps = list(distinct.values())
        try:
            data, _ = await self._gw.complete_json(
                route,
                prompts.equivalence_messages(kind, stem, [r.response or {} for r in reps]),
                purpose="labeling.judge",
                ref=str(qid),
            )
        except DomainError:
            return votes
        rewrite: dict[str, dict[str, Any]] = {}
        groups = data.get("groups")
        if not isinstance(groups, list):
            return votes
        for g in groups:
            if not isinstance(g, list) or not g:
                continue
            idx = [i for i in g if isinstance(i, int) and 0 <= i < len(reps)]
            if not idx:
                continue
            head = reps[idx[0]].response or {}
            for i in idx:
                rewrite[canonical(kind, reps[i].response or {}) or ""] = head
        out = []
        for v in votes:
            c = canonical(kind, v.response) if v.ok and v.response is not None else None
            if c is not None and c in rewrite:
                out.append(SolverVote(v.model, rewrite[c], v.confidence, True))
            else:
                out.append(v)
        return out

    async def _adjudicate(
        self, kind: str, stem: str, payload: dict[str, Any], passage: str | None,
        votes: list[SolverVote], qid: UUID,
    ) -> SolverVote | None:
        route = await self._judge_route(1)
        if route is None:
            return None
        answers = [v.response for v in votes if v.ok and v.response is not None]
        try:
            data, _ = await self._gw.complete_json(
                route, prompts.adjudicate_messages(kind, stem, payload, passage, answers),
                purpose="labeling.adjudicate", ref=str(qid),
            )
        except AIBudgetExhausted:
            raise
        except DomainError:
            return None
        return _vote_from_json(route.model, data)  # type: ignore[arg-type]

    # -- persistence / bank side effects ---------------------------------------------------
    async def _persist(
        self, qid: UUID, trigger: str, d: Decision, stages: list[tuple[str, SolverVote]]
    ) -> UUID:
        run_id = new_id()
        self._s.add(
            SolveRunRow(
                id=run_id, question_id=qid, trigger=trigger, outcome=d.status.value,
                confidence=d.confidence, reason=d.reason, key_conflict=d.key_conflict, response=d.response,
            )
        )
        await self._s.flush()
        for stage, v in stages:
            self._s.add(
                SolverVoteRow(
                    id=new_id(), run_id=run_id, stage=stage, model=v.model, response=v.response,
                    confidence=v.confidence, ok=v.ok,
                )
            )
        await self._s.flush()
        return run_id

    async def _apply(self, q: bank.QuestionDTO, stored: dict[str, Any], d: Decision, run_id: UUID) -> None:
        official = d.reason == "official_key"
        if official and q.options_generated:
            # The key is official but the distractors are AI-made: a human must review the options.
            d = replace(d, status=Status.NEEDS_HUMAN, reason="official_key_generated_options")
            official = False
        if q.status in PROTECTED_STATUSES and not official:
            return  # never downgrade human-reviewed / hidden content
        if official:
            await bank.set_status(self._s, q.id, "verified", MACHINE_ACTOR, f"official key (run {run_id})")
            await self._drop_queue(q.id)
            return
        if d.status is Status.AUTO_AGREED and d.response is not None:
            if canonical(q.kind, d.response) != canonical(q.kind, stored):
                await bank.set_answer(self._s, q.id, d.response, MACHINE_ACTOR)
        await bank.set_status(self._s, q.id, d.status.value, MACHINE_ACTOR, f"{d.reason} (run {run_id})")
        row = await self._s.get(QueueItemRow, q.id)
        if row is None:
            row = QueueItemRow(question_id=q.id, subject_id=q.subject_id, language=q.language)
            self._s.add(row)
        row.state = d.status.value
        row.suggested = d.response
        row.confidence = d.confidence
        row.reason = d.reason
        row.topic_id = q.topic_id
        row.type_id = q.type_id
        row.resolved_at = None
        row.claimed_by = None
        row.claimed_until = None
        await self._s.flush()

    async def _drop_queue(self, qid: UUID) -> None:
        row = await self._s.get(QueueItemRow, qid)
        if row is not None:
            await self._s.delete(row)
            await self._s.flush()
