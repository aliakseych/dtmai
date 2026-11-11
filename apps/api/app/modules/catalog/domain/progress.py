"""Pure derivation of learner progress/state over a path (units of lessons)."""

from dataclasses import dataclass
from typing import Literal

State = Literal["locked", "open", "done"]


@dataclass(frozen=True, slots=True)
class Progress:
    completed_lessons: int
    total_lessons: int
    state: State


def derive_path_progress(
    units: list[list[bool]], start_unit: int = 0
) -> tuple[list[list[Progress]], list[Progress]]:
    """`units[u][l]` = lesson completed. Returns (per-lesson progress, per-unit progress).

    Lessons unlock sequentially: a lesson is `open` while every earlier lesson is done,
    otherwise `locked`; completed lessons are `done` (revisitable). Units before the placement
    `start_unit` are never locked, and the sequence restarts at it. A unit is `done` when all lessons are done,
    `locked` when all of its lessons are locked, else `open`.
    """
    all_prev_done = True
    lesson_out: list[list[Progress]] = []
    unit_out: list[Progress] = []
    for ui, lessons in enumerate(units):
        if ui == start_unit:
            all_prev_done = True  # placement skipped everything before this unit
        row: list[Progress] = []
        for completed in lessons:
            if completed:
                state: State = "done"
            elif all_prev_done or ui < start_unit:
                state = "open"
            else:
                state = "locked"
            row.append(Progress(1 if completed else 0, 1, state))
            all_prev_done = all_prev_done and completed
        lesson_out.append(row)
        done = sum(1 for r in row if r.state == "done")
        if row and done == len(row):
            ustate: State = "done"
        elif row and all(r.state == "locked" for r in row):
            ustate = "locked"
        else:
            ustate = "open"
        unit_out.append(Progress(done, len(row), ustate))
    return lesson_out, unit_out
