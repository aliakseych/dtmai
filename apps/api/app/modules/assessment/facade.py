"""Public assessment facade: other modules import only this."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assessment.infrastructure.repositories import SqlAttemptRepository
from app.modules.assessment.ports import Benchmark, LyceumBenchmarkPort, set_benchmark_port

__all__ = ["Benchmark", "LyceumBenchmarkPort", "has_active_mock", "set_benchmark_port"]


async def has_active_mock(session: AsyncSession, user_id: UUID) -> bool:
    return await SqlAttemptRepository(session).has_active(user_id)
