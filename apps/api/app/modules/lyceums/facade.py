"""Public surface of the lyceums module for other modules."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assessment.facade import Benchmark, set_benchmark_port
from app.modules.lyceums.infrastructure.admission import SqlAdmissionStore
from app.modules.lyceums.infrastructure.orm import YearlyStatRow
from app.shared.db import get_sessionmaker


class LyceumBenchmark:
    """Latest-year benchmark: lowest admin-entered passing score, applications/quota ratio."""

    async def benchmark(self, lyceum_id: UUID) -> Benchmark | None:
        async with get_sessionmaker()() as s:
            year = await s.scalar(
                select(func.max(YearlyStatRow.year)).where(YearlyStatRow.lyceum_id == lyceum_id)
            )
            if year is None:
                return None
            quota, apps, score = (
                await s.execute(
                    select(
                        func.sum(YearlyStatRow.quota),
                        func.sum(YearlyStatRow.applications),
                        func.min(YearlyStatRow.passing_score),
                    ).where(YearlyStatRow.lyceum_id == lyceum_id, YearlyStatRow.year == year)
                )
            ).one()
        ratio = round(apps / quota, 2) if quota else None
        return Benchmark(year=year, passing_score=score, competition_ratio=ratio)


async def lyceum_names(session: AsyncSession, ids: list[UUID]) -> list[str]:
    """Display names of the given lyceums, in the order of `ids` (unknown ids are skipped)."""
    names = await SqlAdmissionStore(session).lyceum_names()
    return [names[i] for i in ids if i in names]


set_benchmark_port(LyceumBenchmark())
