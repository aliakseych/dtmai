"""Server-authoritative mock attempt rules."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

IN_PROGRESS = "in_progress"
SUBMITTED = "submitted"
GRACE = timedelta(seconds=10)  # network slack for the final autosave/submit


def deadline_for(started_at: datetime, duration_min: int) -> datetime:
    return started_at + timedelta(minutes=duration_min)


@dataclass(slots=True)
class MockAttempt:
    id: UUID
    user_id: UUID
    kind: str  # official | generated | personal
    blueprint_id: UUID | None
    blueprint_version: int | None  # pinned at start
    language: str
    started_at: datetime
    deadline: datetime
    questions: list[dict[str, Any]]  # snapshot: id, subject_id, topic_id, type_id, section
    sections: list[dict[str, Any]]  # pinned: subject_id, weight, count
    status: str = IN_PROGRESS
    answers: dict[str, dict[str, Any]] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    result: dict[str, Any] | None = None
    submit_reason: str | None = None  # manual | auto
    submitted_at: datetime | None = None
    score: float | None = None

    @property
    def active(self) -> bool:
        return self.status == IN_PROGRESS

    def expired(self, now: datetime) -> bool:
        return self.active and now >= self.deadline

    def accepts_input(self, now: datetime) -> bool:
        """Edits are accepted until the deadline plus a short grace."""
        return self.active and now <= self.deadline + GRACE

    def time_left(self, now: datetime) -> int:
        return max(0, int((self.deadline - now).total_seconds()))

    def apply_save(
        self, now: datetime, answers: dict[str, dict[str, Any]] | None, flags: list[str] | None
    ) -> bool:
        """Merge an autosave. Returns False (nothing applied) when the attempt no longer accepts input."""
        if not self.accepts_input(now):
            return False
        ids = {str(q["id"]) for q in self.questions}
        for qid, resp in (answers or {}).items():
            if qid in ids:
                if resp:
                    self.answers[qid] = resp
                else:
                    self.answers.pop(qid, None)  # empty response clears the answer
        if flags is not None:
            self.flags = [f for f in dict.fromkeys(flags) if f in ids]
        return True

    def close(self, now: datetime, *, reason: str) -> None:
        self.status = SUBMITTED
        self.submit_reason = reason
        self.submitted_at = min(now, self.deadline + GRACE) if reason == "auto" else now
