from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study_plan.domain.models import Plan, PlanSettings, Task, TaskKind, TaskStatus
from app.modules.study_plan.infrastructure.orm import DailySetRow, PlanRow, TaskRow


def _plan(r: PlanRow) -> Plan:
    return Plan(
        r.id,
        r.user_id,
        PlanSettings.from_json(r.settings),
        r.version,
        r.plan_end,
        r.last_replanned_on,
    )


def _task(r: TaskRow) -> Task:
    return Task(
        r.id,
        r.plan_id,
        r.day,
        r.position,
        TaskKind(r.kind),
        r.subject_id,
        dict(r.target),
        r.est_minutes,
        TaskStatus(r.status),
        r.done_at,
        r.source_ref,
    )


def _row(t: Task) -> TaskRow:
    return TaskRow(
        id=t.id,
        plan_id=t.plan_id,
        day=t.day,
        position=t.position,
        kind=t.kind.value,
        subject_id=t.subject_id,
        target=t.target,
        est_minutes=t.est_minutes,
        status=t.status.value,
        done_at=t.done_at,
        source_ref=t.source_ref,
    )


class SqlPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_plan(self, user_id: UUID) -> Plan | None:
        r = (
            await self._s.execute(select(PlanRow).where(PlanRow.user_id == user_id))
        ).scalar_one_or_none()
        return _plan(r) if r else None

    async def get_plan_for_update(self, user_id: UUID) -> Plan | None:
        """Row-locked read (fresh values): serialises concurrent replans of one plan."""
        q = select(PlanRow).where(PlanRow.user_id == user_id).with_for_update()
        r = (
            await self._s.execute(q.execution_options(populate_existing=True))
        ).scalar_one_or_none()
        return _plan(r) if r else None

    async def insert_plan(self, plan: Plan) -> bool:
        """Create the user's plan; False when a concurrent request already created it."""
        stmt = (
            pg_insert(PlanRow)
            .values(
                id=plan.id,
                user_id=plan.user_id,
                settings=plan.settings.to_json(),
                plan_end=plan.plan_end,
                version=plan.version,
                last_replanned_on=plan.last_replanned_on,
            )
            .on_conflict_do_nothing(index_elements=[PlanRow.user_id])
            .returning(PlanRow.id)
        )
        return (await self._s.execute(stmt)).first() is not None

    async def save_plan(self, plan: Plan) -> None:
        row = await self._s.get(PlanRow, plan.id)
        if row is None:
            row = PlanRow(id=plan.id, user_id=plan.user_id)
            self._s.add(row)
        row.settings = plan.settings.to_json()
        row.plan_end = plan.plan_end
        row.version = plan.version
        row.last_replanned_on = plan.last_replanned_on
        await self._s.flush()

    async def tasks_between(self, plan_id: UUID, start: date, end: date) -> list[Task]:
        q = (
            select(TaskRow)
            .where(TaskRow.plan_id == plan_id, TaskRow.day >= start, TaskRow.day <= end)
            .order_by(TaskRow.day, TaskRow.position)
        )
        return [_task(r) for r in (await self._s.execute(q)).scalars()]

    async def get_task(self, user_id: UUID, task_id: UUID) -> Task | None:
        q = (
            select(TaskRow)
            .join(PlanRow, PlanRow.id == TaskRow.plan_id)
            .where(TaskRow.id == task_id, PlanRow.user_id == user_id)
        )
        r = (await self._s.execute(q)).scalar_one_or_none()
        return _task(r) if r else None

    async def first_open(self, plan_id: UUID, kind: TaskKind, on_or_before: date) -> Task | None:
        q = (
            select(TaskRow)
            .where(
                TaskRow.plan_id == plan_id,
                TaskRow.kind == kind.value,
                TaskRow.status == TaskStatus.TODO.value,
                TaskRow.day <= on_or_before,
            )
            .order_by(TaskRow.day.desc(), TaskRow.position)
            .limit(1)
        )
        r = (await self._s.execute(q)).scalar_one_or_none()
        return _task(r) if r else None

    async def has_source(self, plan_id: UUID, source_ref: UUID) -> bool:
        q = select(TaskRow.id).where(TaskRow.plan_id == plan_id, TaskRow.source_ref == source_ref)
        return (await self._s.execute(q.limit(1))).first() is not None

    async def mark_missed_before(self, plan_id: UUID, day: date) -> None:
        await self._s.execute(
            update(TaskRow)
            .where(TaskRow.plan_id == plan_id, TaskRow.status == "todo", TaskRow.day < day)
            .values(status=TaskStatus.MISSED.value)
        )

    async def delete_todo_from(self, plan_id: UUID, day: date) -> None:
        await self._s.execute(
            delete(TaskRow).where(
                TaskRow.plan_id == plan_id, TaskRow.status == "todo", TaskRow.day >= day
            )
        )

    async def add_tasks(self, tasks: list[Task]) -> None:
        self._s.add_all(_row(t) for t in tasks)
        await self._s.flush()

    async def save_task(self, task: Task) -> None:
        row = await self._s.get(TaskRow, task.id)
        if row is None:
            return
        row.status = task.status.value
        row.done_at = task.done_at
        row.source_ref = task.source_ref
        row.day = task.day
        await self._s.flush()

    async def used_minutes(self, plan_id: UUID, start: date, end: date) -> dict[date, int]:
        q = (
            select(TaskRow.day, func.sum(TaskRow.est_minutes))
            .where(
                TaskRow.plan_id == plan_id,
                TaskRow.day >= start,
                TaskRow.day <= end,
                TaskRow.status != "todo",
            )
            .group_by(TaskRow.day)
        )
        return {d: int(m) for d, m in (await self._s.execute(q)).all()}

    async def count_by_status(
        self, plan_id: UUID, start: date, end: date
    ) -> dict[TaskStatus, tuple[int, int]]:
        """status -> (task count, planned minutes) within the range."""
        q = (
            select(TaskRow.status, func.count(), func.sum(TaskRow.est_minutes))
            .where(TaskRow.plan_id == plan_id, TaskRow.day >= start, TaskRow.day <= end)
            .group_by(TaskRow.status)
        )
        return {
            TaskStatus(s): (int(c), int(m or 0)) for s, c, m in (await self._s.execute(q)).all()
        }

    async def stale_plans(self, today: date) -> list[UUID]:
        """User ids whose plan is still running and was not replanned today."""
        q = select(PlanRow.user_id).where(
            PlanRow.plan_end >= today,
            (PlanRow.last_replanned_on.is_(None)) | (PlanRow.last_replanned_on < today),
        )
        return list((await self._s.execute(q)).scalars())

    async def get_daily_set(self, user_id: UUID, day: date) -> list[UUID] | None:
        r = await self._s.get(DailySetRow, (user_id, day))
        return [UUID(i) for i in r.question_ids] if r else None

    async def save_daily_set(self, user_id: UUID, day: date, ids: list[UUID]) -> None:
        # Concurrent first reads of the day must not fail: the first writer wins.
        await self._s.execute(
            pg_insert(DailySetRow)
            .values(user_id=user_id, day=day, question_ids=[str(i) for i in ids])
            .on_conflict_do_nothing()
        )
