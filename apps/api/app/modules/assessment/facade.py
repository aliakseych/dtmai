"""Public assessment facade: other modules import only this."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assessment.domain.scoring import max_score
from app.modules.assessment.infrastructure.repositories import SqlAttemptRepository
from app.modules.assessment.ports import Benchmark, LyceumBenchmarkPort, set_benchmark_port

__all__ = ["Benchmark", "LyceumBenchmarkPort", "MockResultView", "has_active_mock", "mock_results", "set_benchmark_port"]


async def has_active_mock(session: AsyncSession, user_id: UUID) -> bool:
    return await SqlAttemptRepository(session).has_active(user_id)


@dataclass(frozen=True, slots=True)
class MockResultView:
    mock_id: UUID
    taken_at: datetime
    score: float
    max_score: float


async def mock_results(session: AsyncSession, user_id: UUID, limit: int) -> list[MockResultView]:
    """Submitted mocks, newest first."""
    return [
        MockResultView(
            a.id, a.submitted_at or a.started_at, a.score or 0.0,
            float((a.result or {}).get("max_total") or max_score([s["weight"] for s in a.sections])),
        )
        for a in await SqlAttemptRepository(session).history(user_id, limit)
    ]
