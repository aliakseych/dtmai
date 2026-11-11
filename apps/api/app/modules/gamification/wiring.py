from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.application.service import GamificationService
from app.modules.gamification.infrastructure.profile import IdentityProfile
from app.modules.gamification.infrastructure.repositories import (
    SqlConfigRepository,
    SqlLeagueRepository,
    SqlRewardsRepository,
    SqlSocialRepository,
    SqlStatsRepository,
)
from app.shared.db import get_session
from app.shared.entitlements import entitlements_for
from app.shared.events import Event, subscribe


def build_gamification_service(session: AsyncSession) -> GamificationService:
    return GamificationService(
        SqlStatsRepository(session),
        SqlRewardsRepository(session),
        SqlLeagueRepository(session),
        SqlSocialRepository(session),
        SqlConfigRepository(session),
        IdentityProfile(session),
        entitlements_for,
    )


async def get_gamification_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GamificationService:
    return build_gamification_service(session)


GamificationServiceDep = Annotated[GamificationService, Depends(get_gamification_service)]


@subscribe("SessionCompleted")
async def _on_session_completed(session: AsyncSession, event: Event) -> None:
    p = event.payload
    await build_gamification_service(session).on_session_completed(
        event.id, UUID(p["user_id"]), str(p["session_id"]), p["mode"],
        int(p.get("xp_base", 0)), int(p.get("correct", 0)), int(p.get("total", 0)),
    )


@subscribe("AttemptGraded")
async def _on_attempt_graded(session: AsyncSession, event: Event) -> None:
    p = event.payload
    await build_gamification_service(session).on_attempt_graded(
        event.id, UUID(p["user_id"]), bool(p["correct"])
    )


@subscribe("MockSubmitted")
async def _on_mock_submitted(session: AsyncSession, event: Event) -> None:
    p = event.payload
    await build_gamification_service(session).on_mock_submitted(
        event.id, UUID(p["user_id"]), str(p["attempt_id"])
    )


@subscribe("UserRegistered")
async def _on_user_registered(session: AsyncSession, event: Event) -> None:
    await build_gamification_service(session).on_user_registered(
        event.id, UUID(event.payload["user_id"])
    )
