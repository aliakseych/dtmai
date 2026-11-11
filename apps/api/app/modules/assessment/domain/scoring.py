"""Legacy DTM formula: subject score = sum over sections of (correct / total) * 20 * weight."""

from collections import defaultdict
from dataclasses import dataclass

POINTS_PER_SECTION = 20.0


@dataclass(frozen=True, slots=True)
class Scored:
    section: int
    subject_id: str
    topic_id: str | None
    type_id: str
    correct: bool


@dataclass(frozen=True, slots=True)
class BreakdownRow:
    topic_id: str | None
    type_id: str
    correct: int
    total: int


@dataclass(frozen=True, slots=True)
class ScoreResult:
    total: float
    max_total: float
    subject_scores: dict[str, float]
    correct: int
    answered_total: int
    breakdown: list[BreakdownRow]


def max_score(weights: list[float]) -> float:
    return POINTS_PER_SECTION * sum(weights)


def score(items: list[Scored], weights: list[float]) -> ScoreResult:
    per_section: dict[int, list[Scored]] = defaultdict(list)
    for it in items:
        per_section[it.section].append(it)
    subjects: dict[str, float] = defaultdict(float)
    for idx, group in per_section.items():
        w = weights[idx]
        subjects[group[0].subject_id] += sum(g.correct for g in group) / len(group) * POINTS_PER_SECTION * w
    cells: dict[tuple[str | None, str], list[int]] = defaultdict(lambda: [0, 0])
    for it in items:
        c = cells[(it.topic_id, it.type_id)]
        c[0] += 1 if it.correct else 0
        c[1] += 1
    rows = [BreakdownRow(t, ty, c, n) for (t, ty), (c, n) in sorted(cells.items(), key=lambda kv: str(kv[0]))]
    sub = {k: round(v, 2) for k, v in subjects.items()}
    return ScoreResult(
        round(sum(subjects.values()), 2), max_score(weights), sub, sum(i.correct for i in items), len(items), rows
    )
