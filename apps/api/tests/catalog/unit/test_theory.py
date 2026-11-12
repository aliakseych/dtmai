import pytest

from app.modules.catalog.domain import models as m


def card(title="T", body="b", ex=None):
    return {"title": title, "body_md": body, "example_md": ex}


def test_theory_normalises_cards():
    out = m.validate_theory(
        [{"title": "  Fractions ", "body_md": "$\\frac12$", "example_md": "  "}]
    )
    assert out == [{"title": "Fractions", "body_md": "$\\frac12$", "example_md": None}]


def test_theory_keeps_example_and_order():
    out = m.validate_theory([card("a", ex="x"), card("b")])
    assert [c["title"] for c in out] == ["a", "b"]
    assert out[0]["example_md"] == "x"


def test_theory_max_12_cards():
    assert len(m.validate_theory([card() for _ in range(12)])) == 12
    with pytest.raises(m.Invalid):
        m.validate_theory([card() for _ in range(13)])


@pytest.mark.parametrize(
    "bad", [[card(title="")], [card(title="   ")], [{"body_md": "x"}], ["x"], "x", None]
)
def test_theory_rejects_invalid(bad):
    with pytest.raises(m.Invalid):
        m.validate_theory(bad)


def test_lesson_entity_defaults_theory_empty_and_validates():
    base = {"names": {"en": "L"}, "question_count": 5}
    assert m.validate_entity("lesson", base)["theory"] == []
    assert m.validate_entity("lesson", {**base, "theory": [card()]})["theory"][0]["title"] == "T"
    with pytest.raises(m.Invalid):
        m.validate_entity("lesson", {**base, "theory": [card(title="")]})
