from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.application.service import LearningService
from app.modules.learning.application.stats import StatsService
from app.modules.learning.infrastructure.content import FacadeContent
from app.modules.learning.infrastructure.hearts import FacadeHearts
from app.modules.learning.infrastructure.repositories import SqlLearningRepository
from app.modules.learning.infrastructure.stats import (
    FacadeMockResults,
    FacadeProgress,
    SqlAnswerStats,
)
from app.shared.db import get_session
from app.shared.events import Event, subscribe


def build_learning_service(session: AsyncSession) -> LearningService:
    return LearningService(
        SqlLearningRepository(session), FacadeContent(session), FacadeHearts(session), session
    )


async def get_learning_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LearningService:
    return build_learning_service(session)


def build_stats_service(session: AsyncSession) -> StatsService:
    return StatsService(
        SqlAnswerStats(session), FacadeProgress(session), FacadeMockResults(session)
    )


LearningServiceDep = Annotated[LearningService, Depends(get_learning_service)]


@subscribe("AttemptGraded")
async def _on_attempt_graded(session: AsyncSession, event: Event) -> None:
    await build_learning_service(session).on_mock_attempt(event.id, event.payload)
