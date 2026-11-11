"""Blind stratified audit sampling and labeler agreement stats."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Hashable


def allocate_sample(strata_sizes: Mapping[Hashable, int], sample_size: int) -> dict[Hashable, int]:
    """Proportional allocation with at least one item per non-empty stratum (when the budget allows),
    never exceeding a stratum's size. Deterministic: ties broken by largest remainder, then key repr."""
    sizes = {k: n for k, n in strata_sizes.items() if n > 0}
    total = sum(sizes.values())
    if sample_size <= 0 or total == 0:
        return {}
    sample_size = min(sample_size, total)
    if sample_size < len(sizes):  # fewer slots than strata: keep the largest strata
        keep = sorted(sizes, key=lambda k: (-sizes[k], repr(k)))[:sample_size]
        return dict.fromkeys(keep, 1)
    alloc = dict.fromkeys(sizes, 1)
    remaining = sample_size - len(sizes)
    quotas = {k: sizes[k] * sample_size / total for k in sizes}
    for k in sizes:
        extra = min(sizes[k], int(quotas[k])) - alloc[k]
        if extra > 0:
            take = min(extra, remaining)
            alloc[k] += take
            remaining -= take
    order = sorted(sizes, key=lambda k: (-(quotas[k] - int(quotas[k])), repr(k)))
    while remaining > 0:
        progressed = False
        for k in order:
            if remaining and alloc[k] < sizes[k]:
                alloc[k] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            break
    return alloc


@dataclass(frozen=True, slots=True)
class AgreementStat:
    audited: int
    matched: int

    @property
    def rate(self) -> float | None:
        return None if self.audited == 0 else self.matched / self.audited


def is_audit_match(machine_canonical: str | None, human_canonical: str | None) -> bool:
    return machine_canonical is not None and machine_canonical == human_canonical
