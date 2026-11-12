"""Planning of automatic follow-up generation after an import."""

from collections.abc import Hashable, Mapping
from typing import TypeVar

K = TypeVar("K", bound=Hashable)


def plan_autogen(groups: Mapping[K, int], per_question: int, cap: int) -> list[tuple[K, int]]:
    """Distribute at most `cap` generated questions over groups (group size * per_question each),
    largest groups first; ties broken by key repr. `per_question <= 0` or `cap <= 0` disables."""
    if per_question <= 0 or cap <= 0:
        return []
    plan: list[tuple[K, int]] = []
    remaining = cap
    for key in sorted((k for k, n in groups.items() if n > 0), key=lambda k: (-groups[k], repr(k))):
        if remaining <= 0:
            break
        count = min(groups[key] * per_question, remaining)
        plan.append((key, count))
        remaining -= count
    return plan
