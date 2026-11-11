from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.exam_info.application.service import ExamInfoService
from app.modules.exam_info.infrastructure.repositories import (
    CatalogSubjectDirectory,
    SqlExamInfoRepository,
)
from app.shared.db import get_session


def build_service(session: AsyncSession) -> ExamInfoService:
    return ExamInfoService(SqlExamInfoRepository(session), CatalogSubjectDirectory(session))


async def get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> ExamInfoService:
    return build_service(session)


ServiceDep = Annotated[ExamInfoService, Depends(get_service)]
