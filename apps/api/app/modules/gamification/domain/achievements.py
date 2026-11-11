from dataclasses import dataclass

METRICS = frozenset(
    {"streak_longest", "xp_total", "lessons_completed", "correct_total", "mocks_submitted"}
)


@dataclass(frozen=True, slots=True)
class AchievementDef:
    code: str
    metric: str
    threshold: int
    reward_gems: int


def newly_earned(
    defs: list[AchievementDef], metrics: dict[str, int], already: set[str]
) -> list[AchievementDef]:
    return [
        d
        for d in defs
        if d.code not in already and metrics.get(d.metric, 0) >= d.threshold
    ]
