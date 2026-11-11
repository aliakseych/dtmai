from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Comparison:
    year: int | None
    passing_score: float | None
    competition_ratio: float | None
    gap: float | None  # score - passing_score (positive = above the bar)
    on_track: bool | None


def compare(
    score: float, *, passing_score: float | None, competition_ratio: float | None, year: int | None = None
) -> Comparison:
    gap = round(score - passing_score, 2) if passing_score is not None else None
    return Comparison(year, passing_score, competition_ratio, gap, None if gap is None else gap >= 0)
