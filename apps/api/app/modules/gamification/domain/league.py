"""Weekly leagues: cohorts of ~30 per tier, promotion/demotion at week end (Asia/Tashkent weeks)."""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from uuid import UUID


class Outcome(StrEnum):
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    STAYED = "stayed"


@dataclass(frozen=True, slots=True)
class Standing:
    user_id: UUID
    xp: int
    joined_order: int  # earlier joiners win ties


@dataclass(frozen=True, slots=True)
class Settlement:
    user_id: UUID
    rank: int
    outcome: Outcome


def week_start(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())


def rank_standings(standings: list[Standing]) -> list[Standing]:
    return sorted(standings, key=lambda s: (-s.xp, s.joined_order))


def settle_cohort(
    standings: list[Standing], tier_idx: int, tier_count: int, promote: int, demote: int
) -> list[Settlement]:
    ranked = rank_standings(standings)
    can_promote = tier_idx < tier_count - 1
    promoted = {s.user_id for s in ranked[:promote] if s.xp > 0} if can_promote else set[UUID]()
    # A cohort too small for both zones never demotes: nobody is "bottom" of a tiny group.
    demote_n = demote if tier_idx > 0 and len(ranked) > promote + demote else 0
    demoted = (
        {s.user_id for s in ranked[len(ranked) - demote_n :]} - promoted if demote_n else set()
    )
    out: list[Settlement] = []
    for rank, s in enumerate(ranked, start=1):
        outcome = (
            Outcome.PROMOTED
            if s.user_id in promoted
            else Outcome.DEMOTED
            if s.user_id in demoted
            else Outcome.STAYED
        )
        out.append(Settlement(s.user_id, rank, outcome))
    return out


def next_tier(tier_idx: int, outcome: Outcome, tier_count: int) -> int:
    if outcome is Outcome.PROMOTED:
        return min(tier_count - 1, tier_idx + 1)
    if outcome is Outcome.DEMOTED:
        return max(0, tier_idx - 1)
    return tier_idx


def choose_cohort(open_sizes: dict[UUID, int], cohort_size: int) -> UUID | None:
    """Fill the fullest cohort that still has room; None means open a new one."""
    candidates = [(size, cid) for cid, size in open_sizes.items() if size < cohort_size]
    return max(candidates, key=lambda c: c[0])[1] if candidates else None
