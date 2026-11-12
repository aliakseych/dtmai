from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.wiring import GatewayDep
from app.modules.labeling.application.activity import ActivityService
from app.modules.labeling.application.generation import GenerationService
from app.modules.labeling.application.ingest import IngestService
from app.modules.labeling.application.review import ReviewService
from app.modules.labeling.application.solve import SolveService
from app.modules.labeling.infrastructure.config import get_labeling_settings
from app.shared.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_review_service(session: SessionDep) -> ReviewService:
    return ReviewService(session, audit_ratio=get_labeling_settings().labeling_audit_ratio)


def get_solve_service(session: SessionDep, gw: GatewayDep) -> SolveService:
    s = get_labeling_settings()
    return SolveService(
        session, gw, min_models=s.labeling_min_models, min_confidence=s.labeling_min_confidence
    )


def get_generation_service(session: SessionDep, gw: GatewayDep) -> GenerationService:
    return GenerationService(session, gw)


def get_ingest_service(session: SessionDep, gw: GatewayDep) -> IngestService:
    return IngestService(session, gw)


def get_activity_service(session: SessionDep) -> ActivityService:
    return ActivityService(session)


ReviewDep = Annotated[ReviewService, Depends(get_review_service)]
SolveDep = Annotated[SolveService, Depends(get_solve_service)]
GenerationDep = Annotated[GenerationService, Depends(get_generation_service)]
IngestDep = Annotated[IngestService, Depends(get_ingest_service)]
ActivityDep = Annotated[ActivityService, Depends(get_activity_service)]
