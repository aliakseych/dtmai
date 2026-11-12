from app.shared.errors import DomainError, Forbidden


class AIBudgetExhausted(DomainError):
    status = 429
    code = "ai_budget_exhausted"


class AIUnavailable(DomainError):
    status = 503
    code = "ai_unavailable"


class AIUpstreamFailed(DomainError):
    status = 502
    code = "ai_upstream_failed"


class ExplanationLimitReached(DomainError):
    status = 429
    code = "ai_explanation_limit"


class TutorLimitReached(DomainError):
    status = 429
    code = "ai_tutor_limit"


class FeatureNotEntitled(Forbidden):
    code = "feature_not_entitled"


class GuestNotAllowed(Forbidden):
    code = "guest_not_allowed"


def ensure_registered(roles: frozenset[str] | set[str]) -> None:
    """Ask Temur is for registered users only; guests get a 403 `guest_not_allowed`."""
    if "guest" in roles:
        raise GuestNotAllowed("sign in to chat with Temur")
