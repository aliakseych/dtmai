"""Single entitlements policy port (frozen contract).

`billing` owns the implementation and registers it via `set_entitlements(...)` in its wiring.
Every other module asks only this port; none reads billing tables.
Features and limits are data (admin-configured plans), never hardcoded tiers.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Entitlements:
    plan_code: str  # e.g. "free", "premium" — admin-defined
    features: frozenset[str]  # e.g. {"ai_tutor", "personal_mock", "unlimited_hearts"}
    limits: dict[str, int]  # e.g. {"hearts_max": 5, "ai_explanations_per_day": 3}; -1 = unlimited

    def has(self, feature: str) -> bool:
        return feature in self.features

    def limit(self, key: str, default: int = 0) -> int:
        return self.limits.get(key, default)


class EntitlementsPort(Protocol):
    async def for_user(self, user_id: UUID) -> Entitlements: ...


_FREE_FALLBACK = Entitlements("free", frozenset(), {"hearts_max": 5, "ai_explanations_per_day": 3})
_impl: EntitlementsPort | None = None


def set_entitlements(impl: EntitlementsPort) -> None:
    global _impl
    _impl = impl


async def entitlements_for(user_id: UUID) -> Entitlements:
    return await _impl.for_user(user_id) if _impl else _FREE_FALLBACK
