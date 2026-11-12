import pytest
from pydantic import ValidationError

from app.interfaces.http.v1.identity import MePatch


def test_name_up_to_80_chars_accepted() -> None:
    assert MePatch(name="x" * 80).name == "x" * 80


@pytest.mark.parametrize("name", ["", "x" * 81])
def test_name_outside_1_to_80_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        MePatch(name=name)
