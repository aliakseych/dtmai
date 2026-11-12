"""Pure spend/token accounting for the AI cost ledger and its kill-switches."""

from dataclasses import dataclass

MICRO = 1_000_000


def estimate_cost_micro(
    tokens_in: int, tokens_out: int, price_in_micro_per_mtok: int, price_out_micro_per_mtok: int
) -> int:
    """Cost in micro-USD, rounded up so the ledger never under-reports."""
    if min(tokens_in, tokens_out, price_in_micro_per_mtok, price_out_micro_per_mtok) < 0:
        raise ValueError("negative tokens or price")
    total = tokens_in * price_in_micro_per_mtok + tokens_out * price_out_micro_per_mtok
    return -(-total // MICRO)


def usd_to_micro(usd: float) -> int:
    return round(usd * MICRO)


@dataclass(frozen=True, slots=True)
class Limits:
    enabled: bool  # master switch for AI
    daily_spend_cap_micro: int  # global kill-switch; <=0 disables the cap
    user_daily_token_budget: int  # per user, in+out tokens; <=0 disables the cap


class BudgetExceeded(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def check_call_allowed(
    limits: Limits, *, spent_today_micro: int, user_tokens_today: int | None
) -> None:
    """Raise BudgetExceeded when a new call must not start. `user_tokens_today=None` = system call."""
    if not limits.enabled:
        raise BudgetExceeded("ai_disabled", "AI is switched off")
    if limits.daily_spend_cap_micro > 0 and spent_today_micro >= limits.daily_spend_cap_micro:
        raise BudgetExceeded("ai_spend_cap_reached", "Daily AI spend cap reached")
    if (
        user_tokens_today is not None
        and limits.user_daily_token_budget > 0
        and user_tokens_today >= limits.user_daily_token_budget
    ):
        raise BudgetExceeded("ai_user_budget_reached", "Daily AI token budget reached")


def within_quota(limit: int, used: int) -> bool:
    """Entitlement-style limit: -1 unlimited, 0 none, N per period."""
    return limit < 0 or used < limit


def remaining(limit: int, used: int) -> int:
    """Calls left under `within_quota` semantics: -1 unlimited, never negative."""
    return -1 if limit < 0 else max(0, limit - used)
