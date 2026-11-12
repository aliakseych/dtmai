"""Gap between the predicted exam score and a dream lyceum's passing score. Pure functions."""

from dataclasses import dataclass

MILESTONE_SHARE = 0.25  # a gap above this share of the max score is framed as a next milestone
NEXT_STEP_POINTS = 12.0  # size of one reachable step towards the passing score
QUESTIONS_PER_POINT = 10 / 3  # rough effort heuristic: ~40 practised questions per 12 points


@dataclass(frozen=True, slots=True)
class DreamGap:
    predicted_score: float | None
    max_score: float
    passing_score: float | None
    competition_ratio: float | None
    gap: float | None  # points still missing; <= 0 when the score is already at the bar
    on_track: bool | None
    milestone: bool  # the gap is big: show it as a next milestone, not the whole way
    next_points: float | None  # the reachable step, None when nothing is missing
    next_questions: int | None


def compute_gap(
    predicted: float | None,
    max_score: float,
    passing_score: float | None,
    competition_ratio: float | None,
) -> DreamGap:
    if predicted is None or passing_score is None:
        return DreamGap(
            predicted, max_score, passing_score, competition_ratio, None, None, False, None, None
        )
    gap = round(passing_score - predicted, 1)
    if gap <= 0:
        return DreamGap(
            predicted, max_score, passing_score, competition_ratio, gap, True, False, None, None
        )
    step = round(min(gap, NEXT_STEP_POINTS), 1)
    return DreamGap(
        predicted,
        max_score,
        passing_score,
        competition_ratio,
        gap,
        False,
        gap > max_score * MILESTONE_SHARE,
        step,
        max(1, round(step * QUESTIONS_PER_POINT)),
    )
