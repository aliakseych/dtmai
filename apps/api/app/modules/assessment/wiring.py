from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.wiring import set_active_mock_checker
from app.modules.assessment.application.service import AssessmentService
from app.modules.assessment.infrastructure.adapters import FacadeContent, FacadeUsers
from app.modules.assessment.infrastructure.repositories import SqlAttemptRepository
from app.modules.assessment.ports import get_benchmark_port
from app.shared.db import get_session, get_sessionmaker


def build_assessment_service(session: AsyncSession) -> AssessmentService:
    return AssessmentService(
        SqlAttemptRepository(session),
        FacadeContent(session),
        FacadeUsers(session),
        get_benchmark_port,
        session,
    )


async def get_assessment_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AssessmentService:
    return build_assessment_service(session)


AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]


class _ActiveMock:
    """AI tutor guard: no hints while a mock is running."""

    async def has_active_mock(self, user_id: UUID) -> bool:
        async with get_sessionmaker()() as session:
            return await build_assessment_service(session).has_active(user_id)


set_active_mock_checker(_ActiveMock())
