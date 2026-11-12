"""Solve → judge → escalate state machine (bilimdor-style), pure and framework-free.

Invariants:
- An official answer key always overrides model output and yields `verified`.
- `auto_agreed` only when every responding solver agrees (>= min_models of them) and no official
  key disagrees; auto_agreed questions are never used in mocks (bank/assessment filter by status).
- Models can never produce `verified`; only a human or an official key can.
"""

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.modules.labeling.domain.answers import canonical


class Status(StrEnum):
    DRAFT = "draft"
    AUTO_AGREED = "auto_agreed"
    ESCALATED = "escalated"
    NEEDS_HUMAN = "needs_human"
    VERIFIED = "verified"
    HIDDEN = "hidden"


class Event(StrEnum):
    SOLVE_AGREED = "solve_agreed"
    SOLVE_DISAGREED = "solve_disagreed"
    ESCALATION_DONE = "escalation_done"
    HUMAN_VERIFIED = "human_verified"
    KEY_APPLIED = "key_applied"
    FLAGGED = "flagged"
    AUDIT_MISMATCH = "audit_mismatch"


class IllegalTransition(Exception):
    pass


_TRANSITIONS: dict[tuple[Status, Event], Status] = {
    (Status.DRAFT, Event.SOLVE_AGREED): Status.AUTO_AGREED,
    (Status.DRAFT, Event.SOLVE_DISAGREED): Status.ESCALATED,
    (Status.ESCALATED, Event.SOLVE_AGREED): Status.AUTO_AGREED,
    (Status.ESCALATED, Event.SOLVE_DISAGREED): Status.ESCALATED,
    (Status.ESCALATED, Event.ESCALATION_DONE): Status.NEEDS_HUMAN,
    (Status.NEEDS_HUMAN, Event.SOLVE_AGREED): Status.NEEDS_HUMAN,
    (Status.NEEDS_HUMAN, Event.SOLVE_DISAGREED): Status.NEEDS_HUMAN,
    (Status.AUTO_AGREED, Event.AUDIT_MISMATCH): Status.NEEDS_HUMAN,
}
_ANY_NON_FINAL = (Status.DRAFT, Status.AUTO_AGREED, Status.ESCALATED, Status.NEEDS_HUMAN)


def next_status(current: Status, event: Event) -> Status:
    if event in (Event.HUMAN_VERIFIED, Event.KEY_APPLIED):
        if current is Status.HIDDEN and event is Event.KEY_APPLIED:
            raise IllegalTransition("hidden question cannot take a key")
        return Status.VERIFIED
    if event is Event.FLAGGED:
        return Status.HIDDEN
    try:
        return _TRANSITIONS[(current, event)]
    except KeyError:
        raise IllegalTransition(f"{current.value} --{event.value}--> ?") from None


@dataclass(frozen=True, slots=True)
class SolverVote:
    model: str
    response: dict[str, Any] | None
    confidence: float = 0.0
    ok: bool = True


@dataclass(frozen=True, slots=True)
class Decision:
    status: Status
    response: dict[str, Any] | None  # suggested/final answer
    confidence: float
    reason: str
    key_conflict: bool = False


def _valid(kind: str, votes: list[SolverVote]) -> list[tuple[str, SolverVote]]:
    out: list[tuple[str, SolverVote]] = []
    for v in votes:
        if v.ok and v.response is not None:
            c = canonical(kind, v.response)
            if c is not None:
                out.append((c, v))
    return out


def evaluate_solve(
    kind: str,
    votes: list[SolverVote],
    *,
    official_key: dict[str, Any] | None = None,
    min_models: int = 2,
    min_confidence: float = 0.7,
) -> Decision:
    valid = _valid(kind, votes)
    counts = Counter(c for c, _ in valid)
    plurality: tuple[str, int] | None = counts.most_common(1)[0] if counts else None
    plurality_vote = next(v for c, v in valid if c == plurality[0]) if plurality else None

    if official_key is not None:
        conflict = False
        key_c = canonical(kind, official_key)
        if plurality and len(counts) == 1 and key_c is not None and plurality[0] != key_c:
            conflict = True
        return Decision(Status.VERIFIED, official_key, 1.0, "official_key", key_conflict=conflict)

    if len(valid) < min_models:
        return Decision(Status.ESCALATED, None, 0.0, "insufficient_solvers")
    assert plurality is not None and plurality_vote is not None
    share = plurality[1] / len(valid)
    mean_conf = sum(v.confidence for c, v in valid if c == plurality[0]) / plurality[1]
    if len(counts) == 1:
        if mean_conf < min_confidence:
            return Decision(Status.ESCALATED, plurality_vote.response, mean_conf, "low_confidence")
        return Decision(Status.AUTO_AGREED, plurality_vote.response, mean_conf, "unanimous")
    return Decision(Status.ESCALATED, plurality_vote.response, share * mean_conf, "disagreement")


def evaluate_escalation(kind: str, prior: Decision, adjudicator: SolverVote | None) -> Decision:
    """After adjudication a question always goes to a human; the adjudicator only improves the hint."""
    if adjudicator is None or adjudicator.response is None or not adjudicator.ok:
        return Decision(Status.NEEDS_HUMAN, prior.response, prior.confidence, "no_adjudication")
    adj_c = canonical(kind, adjudicator.response)
    prior_c = canonical(kind, prior.response) if prior.response else None
    if adj_c is None:
        return Decision(Status.NEEDS_HUMAN, prior.response, prior.confidence, "no_adjudication")
    if prior_c == adj_c:
        return Decision(
            Status.NEEDS_HUMAN,
            adjudicator.response,
            max(prior.confidence, adjudicator.confidence),
            "adjudicator_agrees",
        )
    return Decision(
        Status.NEEDS_HUMAN,
        adjudicator.response,
        adjudicator.confidence * 0.5,
        "adjudicator_differs",
    )
