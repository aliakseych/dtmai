import pytest

from app.modules.labeling.domain.activity import activity_action
from app.shared.errors import ValidationFailed


@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        ("accept", "approve"),
        ("edit", "edit"),
        ("flag", "reject"),
        ("skip", "skip"),
        ("bulk", "approve"),
    ],
)
def test_activity_action_mapping(decision, expected):
    assert activity_action(decision) == expected


def test_unknown_action_rejected():
    with pytest.raises(ValidationFailed):
        activity_action("nope")
