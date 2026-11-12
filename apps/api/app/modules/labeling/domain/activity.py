"""Labeler activity vocabulary and aggregate definitions."""

from app.shared.errors import ValidationFailed

ACTIONS = ("claim", "label", "approve", "reject", "edit", "skip", "release")

# Decision actions as stored in labeling.decisions -> activity actions.
_FROM_DECISION = {
    "accept": "approve",
    "edit": "edit",
    "flag": "reject",
    "skip": "skip",
    "bulk": "approve",
}

# Actions that count as a finished piece of work (claims, skips and releases do not).
LABELED = ("label", "approve", "edit", "reject")


def activity_action(decision_action: str) -> str:
    try:
        return _FROM_DECISION[decision_action]
    except KeyError:
        raise ValidationFailed(f"unknown action {decision_action}", code="bad_action") from None
