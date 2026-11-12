from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.modules.learning.domain.stats import STATS_DAYS, UserStats, build_stats
from app.modules.learning.infrastructure.stats import TASHKENT
from app.modules.learning.ports import AnswerStatsPort, MockResultsPort, ProgressPort

MOCK_HISTORY = 20


def _now() -> datetime:
    return datetime.now(UTC)


class StatsService:
    def __init__(
        self,
        answers: AnswerStatsPort,
        progress: ProgressPort,
        mocks: MockResultsPort,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._answers = answers
        self._progress = progress
        self._mocks = mocks
        self._clock = clock

    async def user_stats(self, user_id: UUID) -> UserStats:
        today = self._clock().astimezone(TASHKENT).date()
        since = today - timedelta(days=STATS_DAYS - 1)
        return build_stats(
            await self._progress.progress(user_id, since),
            await self._answers.daily(user_id, since),
            await self._answers.by_subject(user_id),
            await self._mocks.recent(user_id, MOCK_HISTORY),
            today,
        )
