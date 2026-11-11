"""Public surface of exam_info for other modules (study_plan, practice)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.exam_info.domain.models import (
    CertRule,
    Claim,
    ExamEvent,
    ExamProfile,
    Exemption,
    FaqItem,
    Section,
)
from app.modules.exam_info.wiring import build_service

__all__ = [
    "CertRule",
    "Claim",
    "ExamEvent",
    "ExamProfile",
    "Exemption",
    "FaqItem",
    "Section",
    "evaluate_exemptions",
    "list_events",
    "list_faq",
    "profile_for_direction",
]


async def profile_for_direction(session: AsyncSession, direction_code: str) -> ExamProfile | None:
    """Latest active profile (sections, certificate rules, subject choices) of a direction."""
    return await build_service(session).profile_for_direction(direction_code)


async def evaluate_exemptions(
    session: AsyncSession, profile: ExamProfile, claims: list[Claim]
) -> list[Exemption]:
    return await build_service(session).evaluate_exemptions(profile, claims)


async def list_events(session: AsyncSession, exam_year: int | None = None) -> list[ExamEvent]:
    return await build_service(session).list_events(exam_year)


async def list_faq(session: AsyncSession, category: str | None = None) -> list[FaqItem]:
    return await build_service(session).list_faq(category=category)
