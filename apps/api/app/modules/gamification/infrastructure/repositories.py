from datetime import date, datetime
from uuid import UUID

from sqlalchemy import String, column, delete, exists, func, select, table, update
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.domain.achievements import AchievementDef
from app.modules.gamification.domain.config import GameConfig
from app.modules.gamification.domain.hearts import Hearts
from app.modules.gamification.domain.league import Settlement, Standing
from app.modules.gamification.domain.quests import QuestTemplate, UserQuest
from app.modules.gamification.domain.stats import UserStats
from app.modules.gamification.domain.streak import Streak
from app.modules.gamification.infrastructure import orm
from app.modules.gamification.ports import (
    CohortRef,
    LeaderboardRow,
    Membership,
    StandingRow,
    Tier,
)
from app.shared.ids import new_id

# Read-only handle on the identity roles column: guests are anonymous throwaway accounts and
# must never appear in public rankings. Soft reference, no ORM or FK across modules.
_identity_users = table(
    "users", column("id"), column("roles", ARRAY(String(20))), schema="identity"
)


def not_guest(user_id_col):  # type: ignore[no-untyped-def]
    """SQL predicate: the user is not a pure guest (guest role without the student role)."""
    return ~exists(
        select(1).where(
            _identity_users.c.id == user_id_col,
            _identity_users.c.roles.contains(["guest"]),
            ~_identity_users.c.roles.contains(["student"]),
        )
    )


def _to_stats(r: orm.UserStatsRow) -> UserStats:
    return UserStats(
        user_id=r.user_id,
        hearts=Hearts(r.hearts, r.hearts_updated_at),
        xp_total=r.xp_total,
        gems=r.gems,
        streak=Streak(r.streak_current, r.streak_longest, r.streak_last_day, r.streak_freezes),
        lessons_completed=r.lessons_completed,
        correct_total=r.correct_total,
        mocks_submitted=r.mocks_submitted,
        daily_goal_xp=r.daily_goal_xp,
        league_tier=r.league_tier,
        target_lyceum_id=r.target_lyceum_id,
        display_name=r.display_name,
        profile_synced_at=r.profile_synced_at,
    )


class SqlStatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_or_create(self, user_id: UUID, now: datetime, initial_hearts: int) -> UserStats:
        await self._s.execute(
            pg_insert(orm.UserStatsRow)
            .values(user_id=user_id, hearts=initial_hearts, hearts_updated_at=now)
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        row = await self._s.scalar(
            select(orm.UserStatsRow)
            .where(orm.UserStatsRow.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        assert row is not None
        return _to_stats(row)

    async def peek(self, user_id: UUID) -> UserStats | None:
        row = await self._s.get(orm.UserStatsRow, user_id)
        return _to_stats(row) if row else None

    async def save(self, stats: UserStats) -> None:
        await self._s.execute(
            update(orm.UserStatsRow)
            .where(orm.UserStatsRow.user_id == stats.user_id)
            .values(
                xp_total=stats.xp_total,
                gems=stats.gems,
                streak_current=stats.streak.current,
                streak_longest=stats.streak.longest,
                streak_last_day=stats.streak.last_day,
                streak_freezes=stats.streak.freezes,
                hearts=stats.hearts.count,
                hearts_updated_at=stats.hearts.updated_at,
                lessons_completed=stats.lessons_completed,
                correct_total=stats.correct_total,
                mocks_submitted=stats.mocks_submitted,
                daily_goal_xp=stats.daily_goal_xp,
                league_tier=stats.league_tier,
                target_lyceum_id=stats.target_lyceum_id,
                display_name=stats.display_name,
                profile_synced_at=stats.profile_synced_at,
            )
            .execution_options(synchronize_session=False)
        )

    async def mark_event(self, event_id: UUID, handler: str) -> bool:
        res = await self._s.execute(
            pg_insert(orm.ProcessedEventRow)
            .values(event_id=event_id, handler=handler)
            .on_conflict_do_nothing()
        )
        return bool(res.rowcount)  # type: ignore[attr-defined]

    async def log_xp(self, user_id: UUID, day: date, amount: int, ref: str) -> bool:
        res = await self._s.execute(
            pg_insert(orm.XpLogRow)
            .values(id=new_id(), user_id=user_id, day=day, amount=amount, ref=ref)
            .on_conflict_do_nothing(constraint="uq_xp_log_user_ref")
        )
        return bool(res.rowcount)  # type: ignore[attr-defined]

    async def xp_on_day(self, user_id: UUID, day: date) -> int:
        total = await self._s.scalar(
            select(func.coalesce(func.sum(orm.XpLogRow.amount), 0)).where(
                orm.XpLogRow.user_id == user_id, orm.XpLogRow.day == day
            )
        )
        return int(total or 0)

    async def ledger_gems(self, user_id: UUID, delta: int, reason: str, ref: str) -> bool:
        res = await self._s.execute(
            pg_insert(orm.GemLedgerRow)
            .values(id=new_id(), user_id=user_id, delta=delta, reason=reason, ref=ref)
            .on_conflict_do_nothing(constraint="uq_gem_ledger_user_ref")
        )
        return bool(res.rowcount)  # type: ignore[attr-defined]

    async def merge(self, from_id: UUID, into_id: UUID) -> None:
        src = await self._s.get(orm.UserStatsRow, from_id)
        if src is None:
            return
        dst = await self._s.scalar(
            select(orm.UserStatsRow).where(orm.UserStatsRow.user_id == into_id).with_for_update()
        )
        if dst is None:
            await self._s.execute(
                update(orm.UserStatsRow)
                .where(orm.UserStatsRow.user_id == from_id)
                .values(user_id=into_id)
            )
        else:
            dst.xp_total += src.xp_total
            dst.gems += src.gems
            dst.lessons_completed += src.lessons_completed
            dst.correct_total += src.correct_total
            dst.mocks_submitted += src.mocks_submitted
            dst.streak_freezes += src.streak_freezes
            if src.streak_longest > dst.streak_longest:
                dst.streak_longest = src.streak_longest
            if (src.streak_last_day or date.min) >= (dst.streak_last_day or date.min) and (
                src.streak_current > dst.streak_current
            ):
                dst.streak_current = src.streak_current
                dst.streak_last_day = src.streak_last_day
            await self._s.delete(src)
        # Ledgers move over; refs are globally unique per user, so skip clashes by id rewrite.
        await self._s.execute(
            update(orm.XpLogRow)
            .where(
                orm.XpLogRow.user_id == from_id,
                orm.XpLogRow.ref.not_in(
                    select(orm.XpLogRow.ref).where(orm.XpLogRow.user_id == into_id)
                ),
            )
            .values(user_id=into_id)
        )
        await self._s.execute(delete(orm.XpLogRow).where(orm.XpLogRow.user_id == from_id))
        await self._s.execute(
            update(orm.GemLedgerRow)
            .where(
                orm.GemLedgerRow.user_id == from_id,
                orm.GemLedgerRow.ref.not_in(
                    select(orm.GemLedgerRow.ref).where(orm.GemLedgerRow.user_id == into_id)
                ),
            )
            .values(user_id=into_id)
        )
        await self._s.execute(delete(orm.GemLedgerRow).where(orm.GemLedgerRow.user_id == from_id))
        have = select(orm.UserAchievementRow.code).where(orm.UserAchievementRow.user_id == into_id)
        await self._s.execute(
            update(orm.UserAchievementRow)
            .where(
                orm.UserAchievementRow.user_id == from_id, orm.UserAchievementRow.code.not_in(have)
            )
            .values(user_id=into_id)
        )
        await self._s.execute(
            delete(orm.UserAchievementRow).where(orm.UserAchievementRow.user_id == from_id)
        )


def _to_template(r: orm.QuestTemplateRow) -> QuestTemplate:
    return QuestTemplate(
        r.id, r.code, r.metric, r.target, r.reward_gems, r.reward_xp, dict(r.title), r.active
    )


def _to_quest(r: orm.UserQuestRow) -> UserQuest:
    return UserQuest(
        id=r.id,
        template_id=r.template_id,
        code=r.code,
        metric=r.metric,
        title=dict(r.title),
        progress=r.progress,
        target=r.target,
        reward_gems=r.reward_gems,
        reward_xp=r.reward_xp,
        completed=r.completed_at is not None,
    )


class SqlRewardsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def active_templates(self) -> list[QuestTemplate]:
        rows = await self._s.scalars(
            select(orm.QuestTemplateRow).where(orm.QuestTemplateRow.active.is_(True))
        )
        return [_to_template(r) for r in rows]

    async def list_templates(self) -> list[QuestTemplate]:
        rows = await self._s.scalars(
            select(orm.QuestTemplateRow).order_by(orm.QuestTemplateRow.code)
        )
        return [_to_template(r) for r in rows]

    async def get_template(self, template_id: UUID) -> QuestTemplate | None:
        row = await self._s.get(orm.QuestTemplateRow, template_id)
        return _to_template(row) if row else None

    async def save_template(self, t: QuestTemplate) -> None:
        row = await self._s.get(orm.QuestTemplateRow, t.id)
        if row is None:
            row = orm.QuestTemplateRow(id=t.id)
            self._s.add(row)
        row.code, row.metric, row.target = t.code, t.metric, t.target
        row.reward_gems, row.reward_xp = t.reward_gems, t.reward_xp
        row.title, row.active = dict(t.title), t.active
        await self._s.flush()

    async def quests_for_day(self, user_id: UUID, day: date) -> list[UserQuest]:
        rows = await self._s.scalars(
            select(orm.UserQuestRow)
            .where(orm.UserQuestRow.user_id == user_id, orm.UserQuestRow.day == day)
            .order_by(orm.UserQuestRow.code)
        )
        return [_to_quest(r) for r in rows]

    async def add_quests(self, user_id: UUID, day: date, quests: list[UserQuest]) -> None:
        for q in quests:
            await self._s.execute(
                pg_insert(orm.UserQuestRow)
                .values(
                    id=q.id,
                    user_id=user_id,
                    day=day,
                    template_id=q.template_id,
                    code=q.code,
                    metric=q.metric,
                    title=q.title,
                    progress=q.progress,
                    target=q.target,
                    reward_gems=q.reward_gems,
                    reward_xp=q.reward_xp,
                )
                .on_conflict_do_nothing(constraint="uq_user_quests_day")
            )

    async def save_quest(self, q: UserQuest) -> None:
        await self._s.execute(
            update(orm.UserQuestRow)
            .where(orm.UserQuestRow.id == q.id)
            .values(
                progress=q.progress,
                completed_at=func.now() if q.completed else None,
            )
        )

    async def achievement_defs(self) -> list[AchievementDef]:
        rows = await self._s.scalars(
            select(orm.AchievementDefRow).where(orm.AchievementDefRow.active.is_(True))
        )
        return [AchievementDef(r.code, r.metric, r.threshold, r.reward_gems) for r in rows]

    async def earned_codes(self, user_id: UUID) -> set[str]:
        rows = await self._s.scalars(
            select(orm.UserAchievementRow.code).where(orm.UserAchievementRow.user_id == user_id)
        )
        return set(rows)

    async def add_achievement(self, user_id: UUID, code: str) -> bool:
        res = await self._s.execute(
            pg_insert(orm.UserAchievementRow)
            .values(user_id=user_id, code=code)
            .on_conflict_do_nothing()
        )
        return bool(res.rowcount)  # type: ignore[attr-defined]


class SqlLeagueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def tiers(self) -> list[Tier]:
        rows = await self._s.scalars(select(orm.LeagueTierRow).order_by(orm.LeagueTierRow.idx))
        return [
            Tier(r.idx, r.code, dict(r.name), r.cohort_size, r.promote_count, r.demote_count)
            for r in rows
        ]

    async def replace_tiers(self, tiers: list[Tier]) -> None:
        await self._s.execute(delete(orm.LeagueTierRow))
        for t in tiers:
            self._s.add(
                orm.LeagueTierRow(
                    idx=t.idx,
                    code=t.code,
                    name=dict(t.name),
                    cohort_size=t.cohort_size,
                    promote_count=t.promote_count,
                    demote_count=t.demote_count,
                )
            )
        await self._s.flush()

    async def membership(self, user_id: UUID, week: date) -> Membership | None:
        row = (
            await self._s.execute(
                select(orm.LeagueMemberRow, orm.LeagueCohortRow.tier_idx)
                .join(orm.LeagueCohortRow, orm.LeagueCohortRow.id == orm.LeagueMemberRow.cohort_id)
                .where(
                    orm.LeagueMemberRow.user_id == user_id, orm.LeagueMemberRow.week_start == week
                )
            )
        ).first()
        if row is None:
            return None
        m, tier_idx = row
        return Membership(m.cohort_id, tier_idx, m.week_start, m.xp)

    async def open_cohorts(self, week: date, tier_idx: int) -> dict[UUID, int]:
        rows = await self._s.execute(
            select(orm.LeagueCohortRow.id, func.count(orm.LeagueMemberRow.user_id))
            .outerjoin(orm.LeagueMemberRow, orm.LeagueMemberRow.cohort_id == orm.LeagueCohortRow.id)
            .where(orm.LeagueCohortRow.week_start == week, orm.LeagueCohortRow.tier_idx == tier_idx)
            .group_by(orm.LeagueCohortRow.id)
        )
        return {cid: int(n) for cid, n in rows}

    async def create_cohort(self, week: date, tier_idx: int) -> UUID:
        cid = new_id()
        self._s.add(orm.LeagueCohortRow(id=cid, week_start=week, tier_idx=tier_idx))
        await self._s.flush()
        return cid

    async def add_member(self, cohort_id: UUID, user_id: UUID, week: date) -> None:
        order = await self._s.scalar(
            select(func.count()).where(orm.LeagueMemberRow.cohort_id == cohort_id)
        )
        self._s.add(
            orm.LeagueMemberRow(
                cohort_id=cohort_id, user_id=user_id, week_start=week, joined_order=int(order or 0)
            )
        )
        await self._s.flush()

    async def add_xp(self, user_id: UUID, week: date, amount: int) -> None:
        await self._s.execute(
            update(orm.LeagueMemberRow)
            .where(orm.LeagueMemberRow.user_id == user_id, orm.LeagueMemberRow.week_start == week)
            .values(xp=orm.LeagueMemberRow.xp + amount)
        )

    async def standings(self, cohort_id: UUID) -> list[StandingRow]:
        rows = await self._s.execute(
            select(
                orm.LeagueMemberRow.user_id,
                orm.LeagueMemberRow.xp,
                orm.LeagueMemberRow.joined_order,
                orm.UserStatsRow.display_name,
            )
            .outerjoin(orm.UserStatsRow, orm.UserStatsRow.user_id == orm.LeagueMemberRow.user_id)
            .where(orm.LeagueMemberRow.cohort_id == cohort_id)
            .where(not_guest(orm.LeagueMemberRow.user_id))
        )
        return [StandingRow(Standing(uid, xp, order), name or "") for uid, xp, order, name in rows]

    async def unsettled(self, before_week: date) -> list[CohortRef]:
        rows = await self._s.scalars(
            select(orm.LeagueCohortRow)
            .where(
                orm.LeagueCohortRow.settled.is_(False), orm.LeagueCohortRow.week_start < before_week
            )
            .order_by(orm.LeagueCohortRow.week_start)
        )
        return [CohortRef(r.id, r.week_start, r.tier_idx) for r in rows]

    async def settle(self, cohort_id: UUID, results: list[Settlement]) -> None:
        for r in results:
            await self._s.execute(
                update(orm.LeagueMemberRow)
                .where(
                    orm.LeagueMemberRow.cohort_id == cohort_id,
                    orm.LeagueMemberRow.user_id == r.user_id,
                )
                .values(final_rank=r.rank, outcome=r.outcome.value)
            )
        await self._s.execute(
            update(orm.LeagueCohortRow)
            .where(orm.LeagueCohortRow.id == cohort_id)
            .values(settled=True)
        )

    async def set_tier(self, user_id: UUID, tier_idx: int) -> None:
        await self._s.execute(
            update(orm.UserStatsRow)
            .where(orm.UserStatsRow.user_id == user_id)
            .values(league_tier=tier_idx)
        )

    async def merge(self, from_id: UUID, into_id: UUID) -> None:
        # Weeks both have: the destination keeps its membership and gains the guest's xp; move the rest.
        mine = {
            m.week_start: m
            for m in (
                await self._s.scalars(
                    select(orm.LeagueMemberRow).where(orm.LeagueMemberRow.user_id == into_id)
                )
            ).all()
        }
        for m in (
            await self._s.scalars(
                select(orm.LeagueMemberRow).where(orm.LeagueMemberRow.user_id == from_id)
            )
        ).all():
            if m.week_start in mine:
                mine[m.week_start].xp += m.xp
        have = select(orm.LeagueMemberRow.week_start).where(orm.LeagueMemberRow.user_id == into_id)
        await self._s.execute(
            update(orm.LeagueMemberRow)
            .where(
                orm.LeagueMemberRow.user_id == from_id, orm.LeagueMemberRow.week_start.not_in(have)
            )
            .values(user_id=into_id)
        )
        await self._s.execute(
            delete(orm.LeagueMemberRow).where(orm.LeagueMemberRow.user_id == from_id)
        )


class SqlSocialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def follow(self, follower_id: UUID, followee_id: UUID) -> None:
        await self._s.execute(
            pg_insert(orm.FollowRow)
            .values(follower_id=follower_id, followee_id=followee_id)
            .on_conflict_do_nothing()
        )

    async def unfollow(self, follower_id: UUID, followee_id: UUID) -> None:
        await self._s.execute(
            delete(orm.FollowRow).where(
                orm.FollowRow.follower_id == follower_id, orm.FollowRow.followee_id == followee_id
            )
        )

    async def following(self, user_id: UUID) -> list[UUID]:
        rows = await self._s.scalars(
            select(orm.FollowRow.followee_id).where(orm.FollowRow.follower_id == user_id)
        )
        return list(rows)

    async def xp_since(self, user_ids: list[UUID], since: date | None) -> list[LeaderboardRow]:
        if not user_ids:
            return []
        if since is None:
            rows = await self._s.execute(
                select(
                    orm.UserStatsRow.user_id,
                    orm.UserStatsRow.display_name,
                    orm.UserStatsRow.xp_total,
                )
                .where(orm.UserStatsRow.user_id.in_(user_ids))
                .order_by(orm.UserStatsRow.xp_total.desc())
            )
            return [LeaderboardRow(u, n or "", int(x)) for u, n, x in rows]
        xp = func.coalesce(func.sum(orm.XpLogRow.amount), 0)
        rows = await self._s.execute(
            select(orm.UserStatsRow.user_id, orm.UserStatsRow.display_name, xp)
            .outerjoin(
                orm.XpLogRow,
                (orm.XpLogRow.user_id == orm.UserStatsRow.user_id) & (orm.XpLogRow.day >= since),
            )
            .where(orm.UserStatsRow.user_id.in_(user_ids))
            .group_by(orm.UserStatsRow.user_id, orm.UserStatsRow.display_name)
            .order_by(xp.desc())
        )
        return [LeaderboardRow(u, n or "", int(x)) for u, n, x in rows]

    def _lyceum_scores(self, lyceum_id: UUID, since: date | None):  # type: ignore[no-untyped-def]
        if since is None:
            score = orm.UserStatsRow.xp_total
            return select(
                orm.UserStatsRow.user_id.label("user_id"),
                orm.UserStatsRow.display_name.label("name"),
                score.label("xp"),
            ).where(
                orm.UserStatsRow.target_lyceum_id == lyceum_id,
                not_guest(orm.UserStatsRow.user_id),
            )
        xp = func.coalesce(func.sum(orm.XpLogRow.amount), 0)
        return (
            select(
                orm.UserStatsRow.user_id.label("user_id"),
                orm.UserStatsRow.display_name.label("name"),
                xp.label("xp"),
            )
            .outerjoin(
                orm.XpLogRow,
                (orm.XpLogRow.user_id == orm.UserStatsRow.user_id) & (orm.XpLogRow.day >= since),
            )
            .where(
                orm.UserStatsRow.target_lyceum_id == lyceum_id,
                not_guest(orm.UserStatsRow.user_id),
            )
            .group_by(orm.UserStatsRow.user_id, orm.UserStatsRow.display_name)
        )

    async def lyceum_board(
        self, lyceum_id: UUID, since: date | None, limit: int
    ) -> list[LeaderboardRow]:
        sub = self._lyceum_scores(lyceum_id, since).subquery()
        rows = await self._s.execute(
            select(sub.c.user_id, sub.c.name, sub.c.xp).order_by(sub.c.xp.desc()).limit(limit)
        )
        return [LeaderboardRow(u, n or "", int(x)) for u, n, x in rows]

    async def lyceum_rank(self, user_id: UUID, lyceum_id: UUID, since: date | None) -> int | None:
        sub = self._lyceum_scores(lyceum_id, since).subquery()
        mine = await self._s.scalar(select(sub.c.xp).where(sub.c.user_id == user_id))
        if mine is None:
            return None
        ahead = await self._s.scalar(select(func.count()).where(sub.c.xp > mine))
        return int(ahead or 0) + 1

    async def merge(self, from_id: UUID, into_id: UUID) -> None:
        await self._s.execute(delete(orm.FollowRow).where(orm.FollowRow.follower_id == from_id))
        await self._s.execute(delete(orm.FollowRow).where(orm.FollowRow.followee_id == from_id))


class SqlConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self) -> GameConfig:
        row = await self._s.get(orm.GameConfigRow, 1)
        return GameConfig(**row.values) if row else GameConfig()

    async def save(self, config: GameConfig) -> None:
        values = {f: getattr(config, f) for f in config.__slots__}  # type: ignore[attr-defined]
        await self._s.execute(
            pg_insert(orm.GameConfigRow)
            .values(id=1, values=values)
            .on_conflict_do_update(index_elements=["id"], set_={"values": values})
        )
