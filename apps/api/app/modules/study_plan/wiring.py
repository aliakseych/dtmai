from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study_plan.application.service import MODE_TO_KIND, PlanService
from app.modules.study_plan.domain.models import TaskKind
from app.modules.study_plan.infrastructure.adapters import (
    CatalogAdapter,
    DreamAdapter,
    EntitlementAdapter,
    ExamInfoAdapter,
    LearningAdapter,
    QuestionAdapter,
)
from app.modules.study_plan.infrastructure.repositories import SqlPlanRepository
from app.shared.db import get_session
from app.shared.events import Event, subscribe

MAX_DAY_MINUTES = 150


def build_plan_service(session: AsyncSession) -> PlanService:
    return PlanService(
        SqlPlanRepository(session),
        ExamInfoAdapter(session),
        LearningAdapter(session),
        CatalogAdapter(session),
        QuestionAdapter(session),
        EntitlementAdapter(),
        now=lambda: datetime.now(UTC),
        max_day_minutes=MAX_DAY_MINUTES,
        dream=DreamAdapter(session),
    )


async def get_plan_service(session: Annotated[AsyncSession, Depends(get_session)]) -> PlanService:
    return build_plan_service(session)


PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]


@subscribe("SessionCompleted")
async def _on_session_completed(session: AsyncSession, event: Event) -> None:
    kind = MODE_TO_KIND.get(event.payload["mode"])
    if kind is not None:  # placement and other modes have no planned task
        await build_plan_service(session).on_activity(
            event.id, UUID(event.payload["user_id"]), kind
        )


@subscribe("MockSubmitted")
async def _on_mock_submitted(session: AsyncSession, event: Event) -> None:
    p = event.payload
    if not p.get("rewardable") or p.get("kind") == "personal" or not p.get("blueprint_id"):
        return
    await build_plan_service(session).on_activity(
        event.id, UUID(p["user_id"]), TaskKind.MOCK, blueprint_id=UUID(p["blueprint_id"])
    )
