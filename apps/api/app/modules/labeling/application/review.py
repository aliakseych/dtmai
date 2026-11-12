"""Cockpit: queue, decide, undo, bulk approve, blind audit sampling, stats."""

import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank import facade as bank
from app.modules.labeling.application.activity import record_activity
from app.modules.labeling.application.errors import (
    AuditAgreementLow,
    NothingToReview,
    QueueItemGone,
    UndoNotAllowed,
    ValidationFailed,
)
from app.modules.labeling.domain.activity import activity_action
from app.modules.labeling.domain.answers import canonical
from app.modules.labeling.domain.audit import AgreementStat, allocate_sample, is_audit_match
from app.modules.labeling.infrastructure.orm import (
    AuditSampleRow,
    DecisionRow,
    QueueItemRow,
    SolveRunRow,
    SolverVoteRow,
)
from app.shared.errors import Forbidden, NotFound
from app.shared.ids import new_id

CLAIM_TTL = timedelta(minutes=10)
MIN_AUDITED_FOR_GATE = 20


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Review:
    question: bank.QuestionDTO
    state: str
    reason: str
    suggested: dict[str, Any] | None  # None for blind audit items
    confidence: float | None
    audit_sample_id: UUID | None
    votes: list["Vote"] = field(default_factory=list)  # empty for blind audit items


@dataclass(frozen=True, slots=True)
class Vote:
    model: str
    answer: dict[str, Any] | None
    confidence: float


@dataclass(frozen=True, slots=True)
class Filters:
    subject_id: UUID | None = None
    language: str | None = None
    type_id: UUID | None = None
    topic_id: UUID | None = None
    state: str | None = None


def _where(f: Filters) -> list[Any]:
    conds: list[Any] = []
    if f.subject_id:
        conds.append(QueueItemRow.subject_id == f.subject_id)
    if f.language:
        conds.append(QueueItemRow.language == f.language)
    if f.type_id:
        conds.append(QueueItemRow.type_id == f.type_id)
    if f.topic_id:
        conds.append(QueueItemRow.topic_id == f.topic_id)
    if f.state:
        conds.append(QueueItemRow.state == f.state)
    return conds


class ReviewService:
    def __init__(
        self, session: AsyncSession, *, rng: random.Random | None = None, audit_ratio: float = 0.1
    ) -> None:
        self._s = session
        self._rng = rng or random.Random()  # noqa: S311 - sampling, not security
        self._audit_ratio = audit_ratio

    # ---- reading ----------------------------------------------------------------------
    async def list_queue(
        self, f: Filters, limit: int, offset: int
    ) -> tuple[int, list[QueueItemRow]]:
        base = [QueueItemRow.resolved_at.is_(None), *_where(f)]
        total = (
            await self._s.execute(select(func.count()).select_from(QueueItemRow).where(*base))
        ).scalar_one()
        rows = (
            (
                await self._s.execute(
                    select(QueueItemRow)
                    .where(*base)
                    .order_by(
                        _state_rank(), QueueItemRow.confidence.asc(), QueueItemRow.created_at.asc()
                    )
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return total, list(rows)

    async def next_for(self, labeler: UUID, f: Filters, exclude: Sequence[UUID] = ()) -> Review:
        """Claim the next item the client does not already hold (`exclude`).

        Audit samples are interleaved blind (suggestion hidden). A 'claim' activity row is
        written only for a fresh claim, never when re-leasing an item the labeler already holds.
        """
        now = _now()
        if self._audit_ratio > 0 and self._rng.random() < self._audit_ratio:
            audit = await self._claim_audit(f, exclude)
            if audit is not None:
                record_activity(self._s, labeler, "claim", audit.question_id, {"audit": True})
                (q,) = await bank.get_questions(self._s, [audit.question_id])
                return Review(q, "audit", "blind_audit", None, None, audit.id)
        conds = [
            QueueItemRow.resolved_at.is_(None),
            or_(
                QueueItemRow.claimed_until.is_(None),
                QueueItemRow.claimed_until < now,
                QueueItemRow.claimed_by == labeler,
            ),
            ~_skipped_by(labeler),
            ~_audit_pending(),
            *_where(f),
        ]
        if exclude:
            conds.append(QueueItemRow.question_id.not_in(list(exclude)))
        row = (
            await self._s.execute(
                select(QueueItemRow)
                .where(*conds)
                .order_by(
                    _state_rank(), QueueItemRow.confidence.asc(), QueueItemRow.created_at.asc()
                )
                .limit(1)
                .with_for_update(skip_locked=True)
            )
        ).scalar_one_or_none()
        if row is None:
            raise NothingToReview("Nothing to review")
        fresh = row.claimed_by != labeler or row.claimed_until is None or row.claimed_until < now
        row.claimed_by = labeler
        row.claimed_until = now + CLAIM_TTL
        await self._s.flush()
        if fresh:
            record_activity(self._s, labeler, "claim", row.question_id)
        (q,) = await bank.get_questions(self._s, [row.question_id])
        return Review(
            q, row.state, row.reason, row.suggested, row.confidence, None, await self._votes(q.id)
        )

    async def _votes(self, question_id: UUID) -> list[Vote]:
        """Solver votes of the latest solve run for the question."""
        run_id = (
            await self._s.execute(
                select(SolveRunRow.id)
                .where(SolveRunRow.question_id == question_id)
                .order_by(SolveRunRow.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if run_id is None:
            return []
        rows = (
            (
                await self._s.execute(
                    select(SolverVoteRow)
                    .where(
                        SolverVoteRow.run_id == run_id,
                        SolverVoteRow.stage == "solve",
                        SolverVoteRow.ok.is_(True),
                    )
                    .order_by(SolverVoteRow.model)
                )
            )
            .scalars()
            .all()
        )
        return [Vote(r.model, r.response, r.confidence) for r in rows]

    async def get_review(self, question_id: UUID) -> Review:
        row = await self._s.get(QueueItemRow, question_id)
        if row is None:
            raise NotFound("Question is not in the labeling queue")
        (q,) = await bank.get_questions(self._s, [question_id])
        return Review(
            q, row.state, row.reason, row.suggested, row.confidence, None, await self._votes(q.id)
        )

    async def _claim_audit(self, f: Filters, exclude: Sequence[UUID] = ()) -> AuditSampleRow | None:
        conds = [AuditSampleRow.completed_at.is_(None)]
        if f.subject_id:
            conds.append(AuditSampleRow.subject_id == f.subject_id)
        if f.language:
            conds.append(AuditSampleRow.language == f.language)
        if exclude:
            conds.append(AuditSampleRow.question_id.not_in(list(exclude)))
        return (
            await self._s.execute(
                select(AuditSampleRow)
                .where(*conds)
                .order_by(AuditSampleRow.sampled_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
        ).scalar_one_or_none()

    # ---- deciding ---------------------------------------------------------------------
    async def decide(
        self,
        labeler: UUID,
        question_id: UUID,
        *,
        action: str,
        response: dict[str, Any] | None,
        time_ms: int,
        reason: str | None,
        audit_sample_id: UUID | None,
    ) -> DecisionRow:
        if audit_sample_id is not None:
            return await self._decide_audit(
                labeler, question_id, audit_sample_id, response, time_ms
            )
        item = (
            await self._s.execute(
                select(QueueItemRow)
                .where(QueueItemRow.question_id == question_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if item is None or item.resolved_at is not None:
            raise QueueItemGone("Item already resolved or not in queue")
        (q,) = await bank.get_questions(self._s, [question_id])
        prev_answer = (await bank.get_answer_info(self._s, question_id)).response
        d = DecisionRow(
            id=new_id(),
            question_id=question_id,
            labeler_id=labeler,
            action=action,
            response=None,
            time_ms=max(0, time_ms),
            prev_status=q.status,
            new_status=q.status,
            prev_response=prev_answer,
            prev_queue_state=item.state,
            reason=reason,
        )
        actor = str(labeler)
        if action == "skip":
            self._s.add(d)
            item.claimed_by = None
            item.claimed_until = None
        elif action == "flag":
            await bank.set_status(
                self._s, question_id, "hidden", actor, reason or "flagged in labeling"
            )
            d.new_status = "hidden"
            item.resolved_at = _now()
            self._s.add(d)
        elif action in ("accept", "edit"):
            final = item.suggested if action == "accept" else response
            if final is None:
                raise ValidationFailed("response required", code="response_required")
            d.response = final
            if canonical(q.kind, final) != canonical(q.kind, prev_answer):
                await bank.set_answer(self._s, question_id, final, actor)
            await bank.set_status(self._s, question_id, "verified", actor, f"human {action}")
            d.new_status = "verified"
            item.resolved_at = _now()
            self._s.add(d)
        else:
            raise ValidationFailed(f"unknown action {action}", code="bad_action")
        record_activity(
            self._s,
            labeler,
            activity_action(action),
            question_id,
            {"decision_id": str(d.id), **({"reason": reason} if reason else {})},
            d.time_ms,
        )
        await self._s.flush()
        return d

    async def _decide_audit(
        self,
        labeler: UUID,
        question_id: UUID,
        sample_id: UUID,
        response: dict[str, Any] | None,
        time_ms: int,
    ) -> DecisionRow:
        sample = (
            await self._s.execute(
                select(AuditSampleRow).where(AuditSampleRow.id == sample_id).with_for_update()
            )
        ).scalar_one_or_none()
        if sample is None or sample.question_id != question_id:
            raise NotFound("Audit sample not found")
        if sample.completed_at is not None:
            raise QueueItemGone("Audit sample already completed")
        if response is None:
            raise ValidationFailed(
                "blind audit needs an explicit response", code="response_required"
            )
        (q,) = await bank.get_questions(self._s, [question_id])
        match = is_audit_match(
            canonical(q.kind, sample.machine_response or {}), canonical(q.kind, response)
        )
        sample.human_response = response
        sample.labeler_id = labeler
        sample.matched = match
        sample.completed_at = _now()
        d = DecisionRow(
            id=new_id(),
            question_id=question_id,
            labeler_id=labeler,
            action="edit",
            response=response,
            time_ms=max(0, time_ms),
            prev_status=q.status,
            new_status=q.status,
            audit_sample_id=sample_id,
            reason="audit",
        )
        record_activity(
            self._s,
            labeler,
            "label",
            question_id,
            {"audit_sample_id": str(sample_id), "matched": match},
            d.time_ms,
        )
        self._s.add(d)
        if not match:
            await bank.set_answer(self._s, question_id, response, str(labeler))
            await bank.set_status(
                self._s, question_id, "needs_human", str(labeler), "audit mismatch"
            )
            d.new_status = "needs_human"
            item = await self._s.get(QueueItemRow, question_id)
            if item is not None:
                item.state = "needs_human"
                item.reason = "audit_mismatch"
                item.resolved_at = None
                item.claimed_by = None
        await self._s.flush()
        return d

    async def undo(self, actor: UUID, is_admin: bool, decision_id: UUID) -> DecisionRow:
        d = (
            await self._s.execute(
                select(DecisionRow).where(DecisionRow.id == decision_id).with_for_update()
            )
        ).scalar_one_or_none()
        if d is None:
            raise NotFound("Decision not found")
        if d.labeler_id != actor and not is_admin:
            raise Forbidden("Only the author or an admin can undo", code="undo_forbidden")
        if d.undone_at is not None or d.audit_sample_id is not None or d.action == "skip":
            raise UndoNotAllowed("This decision cannot be undone")
        newer = (
            await self._s.execute(
                select(func.count())
                .select_from(DecisionRow)
                .where(
                    DecisionRow.question_id == d.question_id,
                    DecisionRow.created_at > d.created_at,
                    DecisionRow.undone_at.is_(None),
                )
            )
        ).scalar_one()
        if newer:
            raise UndoNotAllowed("A newer decision exists for this question")
        by = str(actor)
        if d.prev_response is not None and d.action in ("accept", "edit", "bulk"):
            await bank.set_answer(self._s, d.question_id, d.prev_response, by)
        if d.prev_status:
            await bank.set_status(self._s, d.question_id, d.prev_status, by, "undo")
        item = await self._s.get(QueueItemRow, d.question_id)
        if item is not None:
            item.resolved_at = None
            item.claimed_by = None
            item.claimed_until = None
            if d.prev_queue_state:
                item.state = d.prev_queue_state
        d.undone_at = _now()
        await self._s.flush()
        return d

    # ---- bulk approve -----------------------------------------------------------------
    async def agreement(self, f: Filters | None = None) -> AgreementStat:
        conds = [AuditSampleRow.completed_at.is_not(None)]
        if f and f.subject_id:
            conds.append(AuditSampleRow.subject_id == f.subject_id)
        if f and f.language:
            conds.append(AuditSampleRow.language == f.language)
        audited, matched = (
            await self._s.execute(
                select(func.count(), func.count().filter(AuditSampleRow.matched.is_(True))).where(
                    *conds
                )
            )
        ).one()
        return AgreementStat(audited, matched)

    async def bulk_approve(
        self,
        labeler: UUID,
        f: Filters,
        *,
        min_confidence: float,
        limit: int,
        min_agreement: float,
        dry_run: bool,
    ) -> tuple[int, int, AgreementStat]:
        stat = await self.agreement(f)
        if stat.audited >= MIN_AUDITED_FOR_GATE and (stat.rate or 0.0) < min_agreement:
            raise AuditAgreementLow(
                f"Audit agreement {stat.rate:.2%} is below {min_agreement:.0%}; review audit mismatches first"
            )
        conds = [
            QueueItemRow.state == "auto_agreed",
            QueueItemRow.resolved_at.is_(None),
            QueueItemRow.confidence >= min_confidence,
            ~_audit_pending(),
            *_where(Filters(f.subject_id, f.language, f.type_id, f.topic_id)),
        ]
        if dry_run:
            n = (
                await self._s.execute(select(func.count()).select_from(QueueItemRow).where(*conds))
            ).scalar_one()
            return min(n, limit), 0, stat
        rows = (
            (
                await self._s.execute(
                    select(QueueItemRow)
                    .where(*conds)
                    .order_by(QueueItemRow.confidence.desc())
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            )
            .scalars()
            .all()
        )
        approved = failed = 0
        for item in rows:
            try:
                async with self._s.begin_nested():
                    prev = (await bank.get_answer_info(self._s, item.question_id)).response
                    await bank.set_status(
                        self._s, item.question_id, "verified", str(labeler), "bulk approve"
                    )
                    self._s.add(
                        DecisionRow(
                            id=new_id(),
                            question_id=item.question_id,
                            labeler_id=labeler,
                            action="bulk",
                            response=item.suggested,
                            prev_status="auto_agreed",
                            new_status="verified",
                            prev_response=prev,
                            prev_queue_state=item.state,
                            reason=f"conf>={min_confidence}",
                        )
                    )
                    record_activity(self._s, labeler, "approve", item.question_id, {"bulk": True})
                    item.resolved_at = _now()
                approved += 1
            except Exception:  # noqa: BLE001 - one bad item must not abort the batch
                failed += 1
        await self._s.flush()
        return approved, failed, stat

    # ---- blind audit --------------------------------------------------------------------
    async def sample_audit(
        self, size: int, f: Filters, rng: random.Random | None = None
    ) -> tuple[UUID, int]:
        r = rng or self._rng
        sampled_ids = select(AuditSampleRow.question_id)
        conds = [
            QueueItemRow.state == "auto_agreed",
            QueueItemRow.resolved_at.is_(None),
            QueueItemRow.suggested.is_not(None),
            QueueItemRow.question_id.not_in(sampled_ids),
            *_where(Filters(f.subject_id, f.language, f.type_id, f.topic_id)),
        ]
        strata = (
            await self._s.execute(
                select(
                    QueueItemRow.subject_id,
                    QueueItemRow.language,
                    QueueItemRow.type_id,
                    func.count(),
                )
                .where(*conds)
                .group_by(QueueItemRow.subject_id, QueueItemRow.language, QueueItemRow.type_id)
            )
        ).all()
        sizes = {(a, b, c): n for a, b, c, n in strata}
        alloc = allocate_sample(sizes, size)
        batch = new_id()
        created = 0
        for (subject_id, language, type_id), n in alloc.items():
            ids = (
                (
                    await self._s.execute(
                        select(QueueItemRow).where(
                            *conds,
                            QueueItemRow.subject_id == subject_id,
                            QueueItemRow.language == language,
                            QueueItemRow.type_id.is_(None)
                            if type_id is None
                            else QueueItemRow.type_id == type_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for item in r.sample(list(ids), min(n, len(ids))):
                self._s.add(
                    AuditSampleRow(
                        id=new_id(),
                        batch_id=batch,
                        question_id=item.question_id,
                        subject_id=subject_id,
                        language=language,
                        machine_response=item.suggested,
                    )
                )
                created += 1
        await self._s.flush()
        return batch, created

    # ---- stats ------------------------------------------------------------------------
    async def stats(self, days: int) -> dict[str, Any]:
        since = _now() - timedelta(days=days)
        per = (
            await self._s.execute(
                select(
                    DecisionRow.labeler_id,
                    DecisionRow.action,
                    func.count(),
                    func.avg(DecisionRow.time_ms),
                )
                .where(DecisionRow.created_at >= since, DecisionRow.undone_at.is_(None))
                .group_by(DecisionRow.labeler_id, DecisionRow.action)
            )
        ).all()
        depth = (
            await self._s.execute(
                select(QueueItemRow.state, func.count())
                .where(QueueItemRow.resolved_at.is_(None))
                .group_by(QueueItemRow.state)
            )
        ).all()
        return {"per_labeler": per, "queue_depth": dict(depth), "audit": await self.agreement()}


def _state_rank() -> Any:
    from sqlalchemy import case

    return case(
        (QueueItemRow.state == "needs_human", 0), (QueueItemRow.state == "escalated", 1), else_=2
    )


def _skipped_by(labeler: UUID) -> Any:
    return (
        select(DecisionRow.id)
        .where(
            DecisionRow.question_id == QueueItemRow.question_id,
            DecisionRow.labeler_id == labeler,
            DecisionRow.action == "skip",
            DecisionRow.undone_at.is_(None),
        )
        .exists()
    )


def _audit_pending() -> Any:
    return (
        select(AuditSampleRow.id)
        .where(
            AuditSampleRow.question_id == QueueItemRow.question_id,
            AuditSampleRow.completed_at.is_(None),
        )
        .exists()
    )
