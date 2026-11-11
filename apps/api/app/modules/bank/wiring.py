from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank.application.service import BankService
from app.modules.bank.facade import service
from app.shared.db import get_session
from app.shared.events import Event, subscribe


async def get_bank_service(session: Annotated[AsyncSession, Depends(get_session)]) -> BankService:
    return service(session)


BankServiceDep = Annotated[BankService, Depends(get_bank_service)]


@subscribe("AttemptGraded")
async def on_attempt_graded(session: AsyncSession, event: Event) -> None:
    """Update question stats; idempotent on event id."""
    p = event.payload
    await service(session).apply_attempt(event.id, UUID(str(p["question_id"])), bool(p["correct"]))
