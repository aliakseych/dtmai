from dataclasses import dataclass
from datetime import timedelta

from app.modules.gamification.domain.xp import XpCaps


@dataclass(frozen=True, slots=True)
class GameConfig:
    """Admin-editable tunables (single row); defaults apply until an admin saves one."""

    heart_refill_minutes: int = 60
    xp_daily_cap: int = 600
    xp_session_cap: int = 150
    xp_per_item_cap: int = 10
    mock_xp: int = 50
    freeze_cost_gems: int = 50
    freeze_max: int = 2
    review_correct_per_heart: int = 3
    daily_quest_count: int = 3

    @property
    def refill_interval(self) -> timedelta:
        return timedelta(minutes=self.heart_refill_minutes)

    @property
    def xp_caps(self) -> XpCaps:
        return XpCaps(self.xp_daily_cap, self.xp_session_cap, self.xp_per_item_cap)
