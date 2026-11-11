"""Adaptive placement: pick the unasked question closest to the current ability estimate."""

from dataclasses import dataclass, field
from uuid import UUID

START_THETA = 1000.0
K = 48.0
MIN_ITEMS = 10
MAX_ITEMS = 12
STABLE_DELTA = 15.0
FLOOR = 800.0
SPAN = 800.0


@dataclass(frozen=True, slots=True)
class PoolItem:
    id: UUID
    difficulty: float


@dataclass(slots=True)
class PlacementState:
    pool: list[PoolItem]
    theta: float = START_THETA
    asked: list[UUID] = field(default_factory=list)
    deltas: list[float] = field(default_factory=list)

    def next_item(self) -> PoolItem | None:
        if self.finished:
            return None
        left = [p for p in self.pool if p.id not in set(self.asked)]
        return min(left, key=lambda p: (abs(p.difficulty - self.theta), str(p.id)), default=None)

    def record(self, item: PoolItem, correct: bool) -> None:
        expected = 1 / (1 + 10 ** ((item.difficulty - self.theta) / 400))
        delta = K * ((1.0 if correct else 0.0) - expected)
        self.theta += delta
        self.asked.append(item.id)
        self.deltas.append(delta)

    @property
    def finished(self) -> bool:
        n = len(self.asked)
        if n >= MAX_ITEMS or n >= len(self.pool):
            return True
        return n >= MIN_ITEMS and all(abs(d) < STABLE_DELTA for d in self.deltas[-2:])


def start_unit_index(theta: float, unit_count: int) -> int:
    if unit_count <= 0:
        return 0
    fraction = min(1.0, max(0.0, (theta - FLOOR) / SPAN))
    return min(unit_count - 1, int(fraction * unit_count))
