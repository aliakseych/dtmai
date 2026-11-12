from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.modules.gamification.application.service import (
    BoardView,
    HeartsView,
    LeagueView,
    StatsView,
)
from app.modules.gamification.domain.config import GameConfig
from app.modules.gamification.domain.quests import METRICS as QUEST_METRICS
from app.modules.gamification.domain.quests import QuestAction, QuestTemplate, quest_action
from app.modules.gamification.ports import LeaderboardRow, Tier
from app.modules.gamification.wiring import GamificationServiceDep
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import ProblemDetails

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

router = APIRouter(tags=["gamification"])
me_router = APIRouter(tags=["gamification"])
admin_router = APIRouter(tags=["gamification-admin"], dependencies=[Depends(require_role("admin"))])


class HeartsOut(BaseModel):
    count: int
    max: int
    unlimited: bool
    next_refill_at: datetime | None

    @classmethod
    def of(cls, h: HeartsView) -> "HeartsOut":
        return cls(count=h.count, max=h.max, unlimited=h.unlimited, next_refill_at=h.next_refill_at)


class TierOut(BaseModel):
    idx: int
    code: str
    name: dict[str, str]
    cohort_size: int
    promote_count: int
    demote_count: int

    @classmethod
    def of(cls, t: Tier) -> "TierOut":
        return cls(**{f: getattr(t, f) for f in cls.model_fields})


class StatsOut(BaseModel):
    user_id: UUID
    xp_total: int
    xp_today: int
    gems: int
    streak: int
    streak_longest: int
    streak_active_today: bool
    streak_at_risk: bool
    streak_freezes: int
    lessons_completed: int
    hearts: HeartsOut
    league_tier: TierOut | None
    today_xp: int
    daily_goal_xp: int
    freeze_cost_gems: int

    @classmethod
    def of(cls, v: StatsView) -> "StatsOut":
        return cls(
            user_id=v.user_id,
            xp_total=v.xp_total,
            xp_today=v.xp_today,
            gems=v.gems,
            streak=v.streak,
            streak_longest=v.streak_longest,
            streak_active_today=v.streak_active_today,
            streak_at_risk=v.streak_at_risk,
            streak_freezes=v.streak_freezes,
            lessons_completed=v.lessons_completed,
            hearts=HeartsOut.of(v.hearts),
            league_tier=TierOut.of(v.league_tier) if v.league_tier else None,
            today_xp=v.xp_today,
            daily_goal_xp=v.daily_goal_xp,
            freeze_cost_gems=v.freeze_cost_gems,
        )


class QuestOut(BaseModel):
    id: UUID
    code: str
    metric: str
    title: dict[str, str]
    progress: int
    target: int
    reward_gems: int
    reward_xp: int
    completed: bool
    action: QuestAction


class LeagueRowOut(BaseModel):
    user_id: UUID
    name: str
    xp: int
    rank: int
    is_me: bool
    zone: Literal["promote", "demote", "safe"]


class LeagueOut(BaseModel):
    tier: TierOut
    week_start: date
    ends_at: datetime
    rows: list[LeagueRowOut]

    @classmethod
    def of(cls, v: LeagueView) -> "LeagueOut":
        return cls(
            tier=TierOut.of(v.tier),
            week_start=v.week_start,
            ends_at=v.ends_at,
            rows=[
                LeagueRowOut(
                    user_id=r.user_id, name=r.name, xp=r.xp, rank=r.rank, is_me=r.is_me, zone=r.zone
                )
                for r in v.rows
            ],  # type: ignore[arg-type]
        )


class LeaderRowOut(BaseModel):
    user_id: UUID
    name: str
    xp: int

    @classmethod
    def of(cls, r: LeaderboardRow) -> "LeaderRowOut":
        return cls(user_id=r.user_id, name=r.name, xp=r.xp)


class BoardOut(BaseModel):
    rows: list[LeaderRowOut]
    my_rank: int | None

    @classmethod
    def of(cls, b: BoardView) -> "BoardOut":
        return cls(rows=[LeaderRowOut.of(r) for r in b.rows], my_rank=b.my_rank)


class AchievementsOut(BaseModel):
    earned: list[str]


# ---------- learner ----------
@me_router.get(
    "/stats", response_model=StatsOut, responses=ERR, operation_id="gamification_me_stats"
)
async def me_stats(user: CurrentUser, svc: GamificationServiceDep) -> StatsOut:
    return StatsOut.of(await svc.me_stats(user.user_id))


class DailyGoalIn(BaseModel):
    xp: Literal[10, 20, 30, 50]


@me_router.put(
    "/daily-goal",
    response_model=StatsOut,
    responses=ERR,
    operation_id="gamification_set_daily_goal",
)
async def set_daily_goal(
    body: DailyGoalIn, user: CurrentUser, svc: GamificationServiceDep
) -> StatsOut:
    return StatsOut.of(await svc.set_daily_goal(user.user_id, body.xp))


@router.get(
    "/quests", response_model=list[QuestOut], responses=ERR, operation_id="gamification_quests"
)
async def quests(user: CurrentUser, svc: GamificationServiceDep) -> list[QuestOut]:
    return [
        QuestOut(
            id=q.id,
            code=q.code,
            metric=q.metric,
            title=q.title,
            progress=q.progress,
            target=q.target,
            reward_gems=q.reward_gems,
            reward_xp=q.reward_xp,
            completed=q.completed,
            action=quest_action(q.metric),
        )
        for q in await svc.quests(user.user_id)
    ]


@router.get(
    "/achievements",
    response_model=AchievementsOut,
    responses=ERR,
    operation_id="gamification_achievements",
)
async def achievements(user: CurrentUser, svc: GamificationServiceDep) -> AchievementsOut:
    return AchievementsOut(earned=await svc.achievements(user.user_id))


@router.get(
    "/leagues/current",
    response_model=LeagueOut | None,
    responses=ERR,
    operation_id="gamification_league_current",
)
async def league_current(user: CurrentUser, svc: GamificationServiceDep) -> LeagueOut | None:
    v = await svc.league_current(user.user_id)
    return LeagueOut.of(v) if v else None


@router.post(
    "/streak/freeze",
    response_model=StatsOut,
    responses=ERR,
    operation_id="gamification_buy_streak_freeze",
)
async def buy_freeze(user: CurrentUser, svc: GamificationServiceDep) -> StatsOut:
    return StatsOut.of(await svc.buy_freeze(user.user_id))


@router.get("/hearts", response_model=HeartsOut, responses=ERR, operation_id="gamification_hearts")
async def hearts(user: CurrentUser, svc: GamificationServiceDep) -> HeartsOut:
    return HeartsOut.of(await svc.hearts_state(user.user_id))


@router.get(
    "/friends",
    response_model=list[LeaderRowOut],
    responses=ERR,
    operation_id="gamification_friends",
)
async def friends(user: CurrentUser, svc: GamificationServiceDep) -> list[LeaderRowOut]:
    return [LeaderRowOut.of(r) for r in await svc.friends(user.user_id)]


@router.post(
    "/friends/{user_id}", status_code=204, responses=ERR, operation_id="gamification_follow"
)
async def follow(user_id: UUID, user: CurrentUser, svc: GamificationServiceDep) -> None:
    await svc.follow(user.user_id, user_id)


@router.delete(
    "/friends/{user_id}", status_code=204, responses=ERR, operation_id="gamification_unfollow"
)
async def unfollow(user_id: UUID, user: CurrentUser, svc: GamificationServiceDep) -> None:
    await svc.unfollow(user.user_id, user_id)


Period = Annotated[Literal["week", "all"], Query()]


@router.get(
    "/leaderboard/lyceum",
    response_model=BoardOut,
    responses=ERR,
    operation_id="gamification_leaderboard_lyceum",
)
async def leaderboard_lyceum(
    user: CurrentUser,
    svc: GamificationServiceDep,
    period: Period = "week",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> BoardOut:
    return BoardOut.of(await svc.lyceum_board(user.user_id, period, limit))


@router.get(
    "/leaderboard/friends",
    response_model=BoardOut,
    responses=ERR,
    operation_id="gamification_leaderboard_friends",
)
async def leaderboard_friends(
    user: CurrentUser, svc: GamificationServiceDep, period: Period = "week"
) -> BoardOut:
    return BoardOut.of(await svc.friends_board(user.user_id, period))


# ---------- admin ----------
class QuestTemplateIn(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    metric: str = Field(description=f"One of: {', '.join(sorted(QUEST_METRICS))}")
    target: int = Field(ge=1)
    reward_gems: int = Field(ge=0, default=0)
    reward_xp: int = Field(ge=0, default=0)
    title: dict[str, str] = Field(default_factory=dict)
    active: bool = True


class QuestTemplateOut(QuestTemplateIn):
    id: UUID

    @classmethod
    def of(cls, t: QuestTemplate) -> "QuestTemplateOut":
        return cls(
            id=t.id,
            code=t.code,
            metric=t.metric,
            target=t.target,
            reward_gems=t.reward_gems,
            reward_xp=t.reward_xp,
            title=t.title,
            active=t.active,
        )


class TiersIn(BaseModel):
    tiers: list[TierOut]


class ConfigModel(BaseModel):
    heart_refill_minutes: int = Field(ge=1)
    xp_daily_cap: int = Field(ge=1)
    xp_session_cap: int = Field(ge=1)
    xp_per_item_cap: int = Field(ge=1)
    mock_xp: int = Field(ge=0)
    freeze_cost_gems: int = Field(ge=0)
    freeze_max: int = Field(ge=0)
    review_correct_per_heart: int = Field(ge=1)
    daily_quest_count: int = Field(ge=0)


class RolloverOut(BaseModel):
    settled_cohorts: int


@admin_router.get(
    "/quest-templates",
    response_model=list[QuestTemplateOut],
    responses=ERR,
    operation_id="gamification_admin_list_quest_templates",
)
async def list_templates(svc: GamificationServiceDep) -> list[QuestTemplateOut]:
    return [QuestTemplateOut.of(t) for t in await svc.list_templates()]


@admin_router.post(
    "/quest-templates",
    response_model=QuestTemplateOut,
    status_code=201,
    responses=ERR,
    operation_id="gamification_admin_create_quest_template",
)
async def create_template(body: QuestTemplateIn, svc: GamificationServiceDep) -> QuestTemplateOut:
    return QuestTemplateOut.of(await svc.save_template(None, **body.model_dump()))


@admin_router.put(
    "/quest-templates/{template_id}",
    response_model=QuestTemplateOut,
    responses=ERR,
    operation_id="gamification_admin_update_quest_template",
)
async def update_template(
    template_id: UUID, body: QuestTemplateIn, svc: GamificationServiceDep
) -> QuestTemplateOut:
    return QuestTemplateOut.of(await svc.save_template(template_id, **body.model_dump()))


@admin_router.get(
    "/league-tiers",
    response_model=list[TierOut],
    responses=ERR,
    operation_id="gamification_admin_get_league_tiers",
)
async def get_tiers(svc: GamificationServiceDep) -> list[TierOut]:
    return [TierOut.of(t) for t in await svc.get_tiers()]


@admin_router.put(
    "/league-tiers",
    response_model=list[TierOut],
    responses=ERR,
    operation_id="gamification_admin_set_league_tiers",
)
async def set_tiers(body: TiersIn, svc: GamificationServiceDep) -> list[TierOut]:
    tiers = [
        Tier(t.idx, t.code, t.name, t.cohort_size, t.promote_count, t.demote_count)
        for t in body.tiers
    ]
    return [TierOut.of(t) for t in await svc.set_tiers(tiers)]


@admin_router.post(
    "/league-rollover",
    response_model=RolloverOut,
    responses=ERR,
    operation_id="gamification_admin_league_rollover",
)
async def rollover(svc: GamificationServiceDep) -> RolloverOut:
    return RolloverOut(settled_cohorts=await svc.rollover())


@admin_router.get(
    "/config",
    response_model=ConfigModel,
    responses=ERR,
    operation_id="gamification_admin_get_config",
)
async def get_config(svc: GamificationServiceDep) -> ConfigModel:
    c = await svc.get_config()
    return ConfigModel(**{f: getattr(c, f) for f in ConfigModel.model_fields})


@admin_router.put(
    "/config",
    response_model=ConfigModel,
    responses=ERR,
    operation_id="gamification_admin_set_config",
)
async def set_config(body: ConfigModel, svc: GamificationServiceDep) -> ConfigModel:
    await svc.set_config(GameConfig(**body.model_dump()))
    return body
