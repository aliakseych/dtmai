from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.gamification.domain.hearts import Hearts
from app.modules.gamification.domain.streak import Streak
from app.shared.errors import Conflict, ValidationFailed

DAILY_GOAL_CHOICES = (10, 20, 30, 50)
DEFAULT_DAILY_GOAL = 20


@dataclass(slots=True)
class UserStats:
    user_id: UUID
    hearts: Hearts
    xp_total: int = 0
    gems: int = 0
    streak: Streak = field(default_factory=Streak)
    lessons_completed: int = 0
    correct_total: int = 0
    mocks_submitted: int = 0
    league_tier: int = 0
    target_lyceum_id: UUID | None = None
    display_name: str = ""
    profile_synced_at: datetime | None = None
    daily_goal_xp: int = DEFAULT_DAILY_GOAL

    def spend_gems(self, cost: int) -> None:
        if self.gems < cost:
            raise Conflict("not enough gems", code="insufficient_gems")
        self.gems -= cost

    def set_daily_goal(self, xp: int) -> None:
        if xp not in DAILY_GOAL_CHOICES:
            raise ValidationFailed("daily goal must be one of 10, 20, 30, 50", code="invalid_daily_goal")
        self.daily_goal_xp = xp

    def metrics(self) -> dict[str, int]:
        return {
            "streak_longest": self.streak.longest,
            "xp_total": self.xp_total,
            "lessons_completed": self.lessons_completed,
            "correct_total": self.correct_total,
            "mocks_submitted": self.mocks_submitted,
        }
