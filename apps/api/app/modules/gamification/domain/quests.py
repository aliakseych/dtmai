"""Daily quests: admin-defined templates, deterministic per-user daily selection."""

from dataclasses import dataclass, field
from datetime import date
from hashlib import sha256
from typing import Literal
from uuid import UUID

METRICS = frozenset(
    {
        "xp_earned",
        "lessons_completed",
        "correct_answers",
        "perfect_sessions",
        "review_sessions",
        "mocks_submitted",
        "streak_kept",
    }
)

QuestAction = Literal["lesson", "drill", "review", "mock", "any"]

_ACTIONS: dict[str, QuestAction] = {
    "lessons_completed": "lesson",
    "perfect_sessions": "lesson",
    "xp_earned": "lesson",
    "streak_kept": "lesson",
    "review_sessions": "review",
    "mocks_submitted": "mock",
    "correct_answers": "drill",
}


def quest_action(metric: str) -> QuestAction:
    """Which learner activity advances this metric (drives the quest's call to action)."""
    return _ACTIONS.get(metric, "any")


@dataclass(frozen=True, slots=True)
class QuestTemplate:
    id: UUID
    code: str
    metric: str
    target: int
    reward_gems: int
    reward_xp: int
    title: dict[str, str] = field(default_factory=dict)
    active: bool = True


def pick_templates(
    templates: list[QuestTemplate], user_id: UUID, day: date, count: int
) -> list[QuestTemplate]:
    """Stable pseudo-random choice so a user sees the same quests all day."""
    def key(t: QuestTemplate) -> str:
        return sha256(f"{user_id}:{day.isoformat()}:{t.code}".encode()).hexdigest()

    return sorted(templates, key=key)[: max(0, count)]


@dataclass(slots=True)
class QuestProgress:
    progress: int
    target: int
    completed: bool = False

    def advance(self, amount: int) -> bool:
        """Add progress; True only on the call that completes the quest."""
        if self.completed or amount <= 0:
            return False
        self.progress = min(self.target, self.progress + amount)
        if self.progress >= self.target:
            self.completed = True
            return True
        return False


@dataclass(slots=True)
class UserQuest:
    """A template snapshot assigned to a user for one Tashkent day."""

    id: UUID
    template_id: UUID
    code: str
    metric: str
    title: dict[str, str]
    progress: int
    target: int
    reward_gems: int
    reward_xp: int
    completed: bool = False
