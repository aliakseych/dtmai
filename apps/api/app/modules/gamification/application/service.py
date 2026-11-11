from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from app.modules.gamification.domain.config import GameConfig
from app.modules.gamification.domain.achievements import newly_earned
from app.modules.gamification.domain.league import (
    next_tier,
    choose_cohort,
    settle_cohort,
    week_start,
)
from app.modules.gamification.domain.quests import (
    METRICS as QUEST_METRICS,
    QuestProgress,
    QuestTemplate,
    UserQuest,
    pick_templates,
)
from app.modules.gamification.domain.stats import UserStats
from app.modules.gamification.domain.streak import tashkent_day
from app.modules.gamification.domain.xp import clamp_session_xp, within_daily_cap
from app.modules.gamification.ports import (
    ConfigRepository,
    LeaderboardRow,
    LeagueRepository,
    ProfilePort,
    RewardsRepository,
    SocialRepository,
    StatsRepository,
    Tier,
)
from app.shared.entitlements import Entitlements
from app.shared.errors import Conflict, NotFound, ValidationFailed
from app.shared.ids import new_id

PROFILE_TTL = timedelta(hours=1)
EntitlementsFn = Callable[[UUID], Awaitable[Entitlements]]


@dataclass(frozen=True, slots=True)
class HeartsView:
    count: int
    max: int
    unlimited: bool
    next_refill_at: datetime | None


@dataclass(frozen=True, slots=True)
class StatsView:
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
    hearts: HeartsView
    league_tier: Tier | None
    daily_goal_xp: int = 20


@dataclass(frozen=True, slots=True)
class LeagueRow:
    user_id: UUID
    name: str
    xp: int
    rank: int
    is_me: bool
    zone: str  # promote | demote | safe


@dataclass(frozen=True, slots=True)
class LeagueView:
    tier: Tier
    week_start: date
    ends_at: datetime
    rows: list[LeagueRow]


@dataclass(frozen=True, slots=True)
class BoardView:
    rows: list[LeaderboardRow]
    my_rank: int | None


class GamificationService:
    def __init__(
        self,
        stats: StatsRepository,
        rewards: RewardsRepository,
        leagues: LeagueRepository,
        social: SocialRepository,
        config: ConfigRepository,
        profile: ProfilePort,
        entitlements: EntitlementsFn,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._stats = stats
        self._rewards = rewards
        self._leagues = leagues
        self._social = social
        self._config = config
        self._profile = profile
        self._ent = entitlements
        self._now = now

    # ---------- shared helpers ----------
    async def _load(self, user_id: UUID) -> tuple[UserStats, GameConfig, int, bool, datetime]:
        now = self._now()
        cfg = await self._config.get()
        ent = await self._ent(user_id)
        unlimited = ent.has("unlimited_hearts")
        hearts_max = max(1, ent.limit("hearts_max", 5))
        stats = await self._stats.get_or_create(user_id, now, hearts_max)
        stats.hearts.refill(now, hearts_max, cfg.refill_interval)
        return stats, cfg, hearts_max, unlimited, now

    async def _sync_profile(self, stats: UserStats, now: datetime, *, force: bool = False) -> None:
        if not force and stats.profile_synced_at and now - stats.profile_synced_at < PROFILE_TTL:
            return
        p = await self._profile.get(stats.user_id)
        if p is not None:
            stats.display_name = p.name
            stats.target_lyceum_id = p.target_lyceum_id
        stats.profile_synced_at = now

    async def _grant_gems(self, stats: UserStats, amount: int, reason: str, ref: str) -> None:
        if amount > 0 and await self._stats.ledger_gems(stats.user_id, amount, reason, ref):
            stats.gems += amount

    async def _award_xp(
        self, stats: UserStats, cfg: GameConfig, day: date, amount: int, ref: str, *, capped: bool
    ) -> int:
        if amount <= 0:
            return 0
        if capped:
            amount = within_daily_cap(amount, await self._stats.xp_on_day(stats.user_id, day), cfg.xp_daily_cap)
        if amount <= 0 or not await self._stats.log_xp(stats.user_id, day, amount, ref):
            return 0
        stats.xp_total += amount
        await self._league_xp(stats, day, amount)
        return amount

    async def _league_xp(self, stats: UserStats, day: date, amount: int) -> None:
        week = week_start(day)
        if await self._leagues.membership(stats.user_id, week) is None:
            tiers = await self._leagues.tiers()
            if not tiers:
                return
            idx = min(max(stats.league_tier, 0), len(tiers) - 1)
            cohort = choose_cohort(await self._leagues.open_cohorts(week, idx), tiers[idx].cohort_size)
            if cohort is None:
                cohort = await self._leagues.create_cohort(week, idx)
            await self._leagues.add_member(cohort, stats.user_id, week)
        await self._leagues.add_xp(stats.user_id, week, amount)

    async def _ensure_quests(self, stats: UserStats, cfg: GameConfig, day: date) -> list[UserQuest]:
        existing = await self._rewards.quests_for_day(stats.user_id, day)
        if existing:
            return existing
        chosen = pick_templates(await self._rewards.active_templates(), stats.user_id, day, cfg.daily_quest_count)
        fresh = [
            UserQuest(new_id(), t.id, t.code, t.metric, dict(t.title), 0, t.target, t.reward_gems, t.reward_xp)
            for t in chosen
        ]
        await self._rewards.add_quests(stats.user_id, day, fresh)
        return await self._rewards.quests_for_day(stats.user_id, day)

    async def _advance(
        self, stats: UserStats, cfg: GameConfig, day: date, metric: str, amount: int
    ) -> None:
        if metric not in QUEST_METRICS or amount <= 0:
            return
        for q in await self._ensure_quests(stats, cfg, day):
            if q.metric != metric or q.completed:
                continue
            prog = QuestProgress(q.progress, q.target)
            done = prog.advance(amount)
            q.progress, q.completed = prog.progress, prog.completed
            await self._rewards.save_quest(q)
            if done:
                await self._grant_gems(stats, q.reward_gems, "quest", f"quest:{q.id}")
                if q.reward_xp:
                    await self._award_xp(stats, cfg, day, q.reward_xp, f"quest:{q.id}", capped=False)

    async def _achievements(self, stats: UserStats) -> None:
        defs = await self._rewards.achievement_defs()
        for d in newly_earned(defs, stats.metrics(), await self._rewards.earned_codes(stats.user_id)):
            if await self._rewards.add_achievement(stats.user_id, d.code):
                await self._grant_gems(stats, d.reward_gems, "achievement", f"ach:{d.code}")

    async def _touch_streak(self, stats: UserStats, cfg: GameConfig, day: date) -> None:
        if stats.streak.record_activity(day).extended:
            await self._advance(stats, cfg, day, "streak_kept", 1)

    # ---------- event handlers ----------
    async def on_session_completed(
        self, event_id: UUID, user_id: UUID, session_id: str, mode: str, xp_base: int, correct: int, total: int
    ) -> None:
        stats, cfg, hearts_max, _, now = await self._load(user_id)
        if not await self._stats.mark_event(event_id, "session_completed"):
            return
        day = tashkent_day(now)
        await self._sync_profile(stats, now)
        xp = clamp_session_xp(xp_base, total, cfg.xp_caps)
        gained = await self._award_xp(stats, cfg, day, xp, f"session:{session_id}", capped=True)
        await self._touch_streak(stats, cfg, day)
        if mode in ("lesson", "drill", "placement"):
            stats.lessons_completed += 1 if mode != "placement" else 0
            await self._advance(stats, cfg, day, "lessons_completed", 1 if mode != "placement" else 0)
            if total and correct == total and mode != "placement":
                await self._advance(stats, cfg, day, "perfect_sessions", 1)
        if mode == "review":
            await self._advance(stats, cfg, day, "review_sessions", 1)
            stats.hearts.gain(correct // max(1, cfg.review_correct_per_heart), hearts_max)
        await self._advance(stats, cfg, day, "xp_earned", gained)
        await self._achievements(stats)
        await self._stats.save(stats)

    async def on_attempt_graded(self, event_id: UUID, user_id: UUID, correct: bool) -> None:
        stats, cfg, _, _, now = await self._load(user_id)
        if not await self._stats.mark_event(event_id, "attempt_graded"):
            return
        if correct:
            stats.correct_total += 1
            await self._advance(stats, cfg, tashkent_day(now), "correct_answers", 1)
            await self._achievements(stats)
        await self._stats.save(stats)

    async def on_mock_submitted(self, event_id: UUID, user_id: UUID, attempt_id: str) -> None:
        stats, cfg, _, _, now = await self._load(user_id)
        if not await self._stats.mark_event(event_id, "mock_submitted"):
            return
        day = tashkent_day(now)
        await self._sync_profile(stats, now)
        gained = await self._award_xp(stats, cfg, day, cfg.mock_xp, f"mock:{attempt_id}", capped=True)
        stats.mocks_submitted += 1
        await self._touch_streak(stats, cfg, day)
        await self._advance(stats, cfg, day, "mocks_submitted", 1)
        await self._advance(stats, cfg, day, "xp_earned", gained)
        await self._achievements(stats)
        await self._stats.save(stats)

    async def on_user_registered(self, event_id: UUID, user_id: UUID) -> None:
        stats, _, _, _, now = await self._load(user_id)
        if await self._stats.mark_event(event_id, "user_registered"):
            await self._sync_profile(stats, now, force=True)
        await self._stats.save(stats)

    # ---------- hearts / streak freeze ----------
    def _hearts_view(self, stats: UserStats, cfg: GameConfig, hearts_max: int, unlimited: bool) -> HeartsView:
        return HeartsView(
            stats.hearts.count,
            hearts_max,
            unlimited,
            None if unlimited else stats.hearts.next_refill_at(hearts_max, cfg.refill_interval),
        )

    async def hearts_state(self, user_id: UUID) -> HeartsView:
        stats, cfg, hearts_max, unlimited, _ = await self._load(user_id)
        await self._stats.save(stats)
        return self._hearts_view(stats, cfg, hearts_max, unlimited)

    async def lose_heart(self, user_id: UUID) -> HeartsView:
        stats, cfg, hearts_max, unlimited, now = await self._load(user_id)
        stats.hearts.lose(now, hearts_max, cfg.refill_interval, unlimited=unlimited)
        await self._stats.save(stats)
        return self._hearts_view(stats, cfg, hearts_max, unlimited)

    async def buy_freeze(self, user_id: UUID) -> StatsView:
        stats, cfg, _, _, now = await self._load(user_id)
        if stats.streak.freezes >= cfg.freeze_max:
            raise Conflict("freeze limit reached", code="freeze_limit")
        stats.spend_gems(cfg.freeze_cost_gems)
        stats.streak.add_freeze(cfg.freeze_max)
        await self._stats.ledger_gems(user_id, -cfg.freeze_cost_gems, "freeze", f"freeze:{new_id()}")
        await self._stats.save(stats)
        return await self._view(stats, cfg)

    # ---------- reads ----------
    async def _view(self, stats: UserStats, cfg: GameConfig) -> StatsView:
        now = self._now()
        today = tashkent_day(now)
        ent = await self._ent(stats.user_id)
        hearts_max = max(1, ent.limit("hearts_max", 5))
        tiers = await self._leagues.tiers()
        tier = tiers[min(max(stats.league_tier, 0), len(tiers) - 1)] if tiers else None
        s = stats.streak
        return StatsView(
            stats.user_id,
            stats.xp_total,
            await self._stats.xp_on_day(stats.user_id, today),
            stats.gems,
            s.current_on(today),
            s.longest,
            s.active_on(today),
            s.at_risk_on(today),
            s.freezes,
            stats.lessons_completed,
            self._hearts_view(stats, cfg, hearts_max, ent.has("unlimited_hearts")),
            tier,
            stats.daily_goal_xp,
        )

    async def set_daily_goal(self, user_id: UUID, xp: int) -> StatsView:
        stats, cfg, _, _, _ = await self._load(user_id)
        stats.set_daily_goal(xp)
        await self._stats.save(stats)
        return await self._view(stats, cfg)

    async def me_stats(self, user_id: UUID) -> StatsView:
        stats, cfg, _, _, now = await self._load(user_id)
        await self._sync_profile(stats, now, force=True)
        await self._stats.save(stats)
        return await self._view(stats, cfg)

    async def quests(self, user_id: UUID) -> list[UserQuest]:
        stats, cfg, _, _, now = await self._load(user_id)
        quests = await self._ensure_quests(stats, cfg, tashkent_day(now))
        await self._stats.save(stats)
        return quests

    async def achievements(self, user_id: UUID) -> list[str]:
        return sorted(await self._rewards.earned_codes(user_id))

    async def league_current(self, user_id: UUID) -> LeagueView | None:
        stats, _, _, _, now = await self._load(user_id)
        tiers = await self._leagues.tiers()
        if not tiers:
            return None
        week = week_start(tashkent_day(now))
        m = await self._leagues.membership(user_id, week)
        if m is None:
            await self._league_xp(stats, tashkent_day(now), 0)
            m = await self._leagues.membership(user_id, week)
            await self._stats.save(stats)
        if m is None:
            return None
        tier = tiers[m.tier_idx]
        from app.modules.gamification.domain.league import rank_standings

        rows = await self._leagues.standings(m.cohort_id)
        names = {r.standing.user_id: r.name for r in rows}
        ranked = rank_standings([r.standing for r in rows])
        n = len(ranked)
        can_promote = m.tier_idx < len(tiers) - 1
        demote_n = tier.demote_count if m.tier_idx > 0 and n > tier.promote_count + tier.demote_count else 0
        out = []
        for i, s in enumerate(ranked, start=1):
            zone = (
                "promote" if can_promote and i <= tier.promote_count and s.xp > 0
                else "demote" if demote_n and i > n - demote_n
                else "safe"
            )
            out.append(LeagueRow(s.user_id, names.get(s.user_id, ""), s.xp, i, s.user_id == user_id, zone))
        ends = datetime.combine(week + timedelta(days=7), datetime.min.time(), tzinfo=tashkent_tz())
        return LeagueView(tier, week, ends.astimezone(UTC), out)

    async def follow(self, me: UUID, other: UUID) -> None:
        if me == other:
            raise ValidationFailed("cannot follow yourself", code="self_follow")
        if await self._stats.peek(other) is None:
            raise NotFound("user not found", code="user_not_found")
        await self._social.follow(me, other)

    async def unfollow(self, me: UUID, other: UUID) -> None:
        await self._social.unfollow(me, other)

    async def friends(self, me: UUID) -> list[LeaderboardRow]:
        ids = await self._social.following(me)
        return await self._social.xp_since(ids, week_start(tashkent_day(self._now())))

    async def friends_board(self, me: UUID, period: str) -> BoardView:
        ids = [*await self._social.following(me), me]
        since = week_start(tashkent_day(self._now())) if period == "week" else None
        rows = await self._social.xp_since(ids, since)
        rank = next((i for i, r in enumerate(rows, 1) if r.user_id == me), None)
        return BoardView(rows, rank)

    async def lyceum_board(self, me: UUID, period: str, limit: int) -> BoardView:
        stats, _, _, _, now = await self._load(me)
        await self._sync_profile(stats, now)
        await self._stats.save(stats)
        if stats.target_lyceum_id is None:
            return BoardView([], None)
        since = week_start(tashkent_day(now)) if period == "week" else None
        rows = await self._social.lyceum_board(stats.target_lyceum_id, since, limit)
        rank = await self._social.lyceum_rank(me, stats.target_lyceum_id, since)
        return BoardView(rows, rank)

    # ---------- weekly rollover ----------
    async def rollover(self) -> int:
        """Settle every finished week's cohorts: record ranks, move users between tiers. Idempotent."""
        tiers = {t.idx: t for t in await self._leagues.tiers()}
        if not tiers:
            return 0
        current = week_start(tashkent_day(self._now()))
        settled = 0
        for cohort in await self._leagues.unsettled(current):
            tier = tiers.get(cohort.tier_idx)
            if tier is None:
                continue
            rows = await self._leagues.standings(cohort.id)
            results = settle_cohort(
                [r.standing for r in rows], cohort.tier_idx, len(tiers), tier.promote_count, tier.demote_count
            )
            await self._leagues.settle(cohort.id, results)
            for r in results:
                await self._leagues.set_tier(r.user_id, next_tier(cohort.tier_idx, r.outcome, len(tiers)))
            settled += 1
        return settled

    # ---------- merge ----------
    async def merge_guest(self, from_id: UUID, into_id: UUID) -> None:
        if from_id == into_id:
            return
        await self._stats.merge(from_id, into_id)
        await self._leagues.merge(from_id, into_id)
        await self._social.merge(from_id, into_id)

    # ---------- admin ----------
    async def list_templates(self) -> list[QuestTemplate]:
        return await self._rewards.list_templates()

    async def save_template(
        self, template_id: UUID | None, *, code: str, metric: str, target: int,
        reward_gems: int, reward_xp: int, title: dict[str, str], active: bool,
    ) -> QuestTemplate:
        if metric not in QUEST_METRICS:
            raise ValidationFailed(f"unknown metric {metric}", code="unknown_metric")
        if target < 1 or reward_gems < 0 or reward_xp < 0:
            raise ValidationFailed("invalid quest numbers", code="invalid_quest")
        if template_id is not None and await self._rewards.get_template(template_id) is None:
            raise NotFound("quest template not found", code="quest_template_not_found")
        t = QuestTemplate(template_id or new_id(), code, metric, target, reward_gems, reward_xp, title, active)
        await self._rewards.save_template(t)
        return t

    async def get_tiers(self) -> list[Tier]:
        return await self._leagues.tiers()

    async def set_tiers(self, tiers: list[Tier]) -> list[Tier]:
        if not tiers or [t.idx for t in tiers] != list(range(len(tiers))):
            raise ValidationFailed("tier idx must be 0..n-1 in order", code="invalid_tiers")
        if any(t.cohort_size < 2 or t.promote_count < 0 or t.demote_count < 0 for t in tiers):
            raise ValidationFailed("invalid tier sizes", code="invalid_tiers")
        await self._leagues.replace_tiers(tiers)
        return tiers

    async def get_config(self) -> GameConfig:
        return await self._config.get()

    async def set_config(self, config: GameConfig) -> GameConfig:
        if min(config.heart_refill_minutes, config.xp_daily_cap, config.xp_session_cap,
               config.xp_per_item_cap, config.review_correct_per_heart) < 1:
            raise ValidationFailed("config values must be positive", code="invalid_config")
        await self._config.save(replace(config))
        return config


def tashkent_tz():  # type: ignore[no-untyped-def]
    from app.modules.gamification.domain.streak import TASHKENT

    return TASHKENT
