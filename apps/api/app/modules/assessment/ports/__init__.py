from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Item:
    id: UUID
    subject_id: UUID
    topic_id: UUID | None
    type_id: UUID
    kind: str
    language: str
    stem: str
    media: list[Any]
    payload: dict[str, Any]
    passage_id: UUID | None
    children: list["Item"] = field(default_factory=list)  # passage_group only


@dataclass(frozen=True, slots=True)
class Graded:
    correct: bool
    correct_response: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Blueprint:
    id: UUID
    code: str
    names: dict[str, str]
    kind: str
    version: int
    duration_min: int
    sections: list[dict[str, Any]]
    source_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class WeakSpot:
    topic_id: UUID | None
    type_id: UUID


@dataclass(frozen=True, slots=True)
class Benchmark:
    year: int | None
    passing_score: float | None
    competition_ratio: float | None


class ContentPort(Protocol):
    async def blueprint(self, blueprint_id: UUID) -> Blueprint | None: ...
    async def blueprints(self) -> list[Blueprint]: ...
    async def items(self, ids: Sequence[UUID]) -> list[Item]: ...
    async def pick(
        self, *, subject_id: UUID, topic_ids: Sequence[UUID] | None, type_ids: Sequence[UUID] | None,
        language: str, n: int, exclude_ids: Sequence[UUID] = (),
    ) -> list[Item]: ...
    async def grade(self, question_id: UUID, response: dict[str, Any]) -> Graded: ...
    async def weak_spots(self, user_id: UUID, subject_id: UUID) -> list[WeakSpot]: ...


class UserPort(Protocol):
    async def has_feature(self, user_id: UUID, feature: str) -> bool: ...
    async def target_lyceum_id(self, user_id: UUID) -> UUID | None: ...


class LyceumBenchmarkPort(Protocol):
    """Implemented by the lyceums module (competition ratio / passing score)."""

    async def benchmark(self, lyceum_id: UUID) -> Benchmark | None: ...


class NoBenchmark:
    async def benchmark(self, lyceum_id: UUID) -> Benchmark | None:
        return None


_benchmark: LyceumBenchmarkPort = NoBenchmark()


def set_benchmark_port(port: LyceumBenchmarkPort) -> None:
    """Called by the lyceums module at import time to plug in real data."""
    global _benchmark
    _benchmark = port


def get_benchmark_port() -> LyceumBenchmarkPort:
    return _benchmark
