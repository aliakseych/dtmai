"""Labeler activity log: recording, paged listing and per-labeler leaderboard."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.labeling.domain.activity import ACTIONS, LABELED
from app.modules.labeling.infrastructure.orm import ActivityRow
from app.shared.errors import ValidationFailed
from app.shared.ids import new_id

ACTIVITY_SORTS = {
    "created_at": ActivityRow.created_at,
    "duration_ms": ActivityRow.duration_ms,
    "action": ActivityRow.action,
}
LEADERBOARD_SORTS = ("labeled", "approved", "rejected", "avg_duration")


def record_activity(
    session: AsyncSession,
    actor: UUID,
    action: str,
    question_id: UUID | None,
    payload: dict[str, Any] | None = None,
    duration_ms: int | None = None,
) -> ActivityRow:
    """Queue one activity row on the caller's transaction (flushed with the surrounding work)."""
    row = ActivityRow(
        id=new_id(),
        actor_user_id=actor,
        action=action,
        question_id=question_id,
        payload=payload or {},
        duration_ms=duration_ms,
    )
    session.add(row)
    return row


@dataclass(frozen=True, slots=True)
class LeaderboardEntry:
    actor_id: UUID
    labeled: int
    approved: int
    rejected: int
    avg_duration_ms: float | None
    last_active_at: datetime | None


def _window(stmt: Select[Any], start: datetime | None, end: datetime | None) -> Select[Any]:
    if start is not None:
        stmt = stmt.where(ActivityRow.created_at >= start)
    if end is not None:
        stmt = stmt.where(ActivityRow.created_at < end)
    return stmt


class ActivityService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_activity(
        self,
        *,
        actor_id: UUID | None,
        action: str | None,
        start: datetime | None,
        end: datetime | None,
        sort: str,
        descending: bool,
        page: int,
        size: int,
    ) -> tuple[int, list[ActivityRow]]:
        if action is not None and action not in ACTIONS:
            raise ValidationFailed(f"unknown action {action}", code="bad_action")
        column = ACTIVITY_SORTS.get(sort)
        if column is None:
            raise ValidationFailed(f"unknown sort {sort}", code="bad_sort")
        conds = []
        if actor_id is not None:
            conds.append(ActivityRow.actor_user_id == actor_id)
        if action is not None:
            conds.append(ActivityRow.action == action)
        base = _window(select(ActivityRow).where(*conds), start, end)
        total = (
            await self._s.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        order = column.desc() if descending else column.asc()
        rows = (
            (
                await self._s.execute(
                    base.order_by(order, ActivityRow.id).limit(size).offset((page - 1) * size)
                )
            )
            .scalars()
            .all()
        )
        return total, list(rows)

    async def leaderboard(
        self, *, start: datetime | None, end: datetime | None, sort: str, descending: bool
    ) -> list[LeaderboardEntry]:
        if sort not in LEADERBOARD_SORTS:
            raise ValidationFailed(f"unknown sort {sort}", code="bad_sort")
        a = ActivityRow
        is_decision = a.action.in_(LABELED + ("skip",))
        stmt = _window(
            select(
                a.actor_user_id,
                func.count().filter(a.action.in_(LABELED)),
                func.count().filter(a.action == "approve"),
                func.count().filter(a.action == "reject"),
                func.avg(case((is_decision, a.duration_ms))),
                func.max(a.created_at),
            ).group_by(a.actor_user_id),
            start,
            end,
        )
        entries = [
            LeaderboardEntry(r[0], r[1], r[2], r[3], None if r[4] is None else float(r[4]), r[5])
            for r in (await self._s.execute(stmt)).all()
        ]
        return sort_leaderboard(entries, sort, descending)


def sort_leaderboard(
    entries: list[LeaderboardEntry], sort: str, descending: bool
) -> list[LeaderboardEntry]:
    """Missing averages sort last in either direction."""
    key = {
        "labeled": lambda e: e.labeled,
        "approved": lambda e: e.approved,
        "rejected": lambda e: e.rejected,
        "avg_duration": lambda e: e.avg_duration_ms,
    }[sort]
    known = sorted((e for e in entries if key(e) is not None), key=key, reverse=descending)
    return known + [e for e in entries if key(e) is None]
