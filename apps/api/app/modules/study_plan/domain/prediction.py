"""Predicted exam score and countdown. Pure functions."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.modules.study_plan.domain.exam import ROLE_CREATIVE, ExamSection

TAPER_MIN, TAPER_MAX = 5, 7


def predicted_score(
    sections: tuple[ExamSection, ...],
    exempt: dict[UUID, float],
    mastery: dict[UUID, float | None],
    chosen: dict[UUID, UUID | None],
    max_score: float,
) -> float:
    """Points = max_points x mastery per section; exempt sections count in full.

    Unknown mastery counts as 0 (nothing demonstrated). Creative sections are not in the app and
    add nothing. The total is bounded to [0, max_score] (146 for the lyceum exam).
    """
    total = 0.0
    for s in sections:
        if s.role == ROLE_CREATIVE:
            continue
        if s.section_id in exempt:
            total += s.max_points * exempt[s.section_id]
            continue
        subject = s.subject_id or chosen.get(s.section_id)
        m = mastery.get(subject) if subject else None
        total += s.max_points * min(max(m or 0.0, 0.0), 1.0)
    return round(min(max(total, 0.0), max_score), 1)


def clamp_taper(days: int) -> int:
    return min(max(days, TAPER_MIN), TAPER_MAX)


@dataclass(frozen=True, slots=True)
class Countdown:
    exam_date: date
    plan_end: date
    days_left: int  # to the exam, 0 on exam day, never negative
    days_to_plan_end: int
    phase: str  # preparing | taper | exam_over


def countdown(today: date, exam_date: date, taper_days: int) -> Countdown:
    end = exam_date.fromordinal(exam_date.toordinal() - clamp_taper(taper_days))
    if today > exam_date:
        phase = "exam_over"
    elif today > end:
        phase = "taper"
    else:
        phase = "preparing"
    return Countdown(
        exam_date, end, max((exam_date - today).days, 0), max((end - today).days, 0), phase
    )
