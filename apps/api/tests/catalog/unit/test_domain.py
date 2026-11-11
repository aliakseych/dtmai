import pytest

from app.modules.catalog.domain import models as m

U1 = "11111111-1111-1111-1111-111111111111"
U2 = "22222222-2222-2222-2222-222222222222"


def test_names_require_known_locale():
    assert m.validate_names({"ru": " Привет "}) == {"ru": "Привет"}
    with pytest.raises(m.Invalid):
        m.validate_names({"de": "x"})
    with pytest.raises(m.Invalid):
        m.validate_names({"en": "  "})


def test_pick_name_falls_back():
    assert m.pick_name({"ru": "a"}, "en") == "a"
    assert m.pick_name({"en": "e", "ru": "r"}, "ru") == "r"


def test_code_rules():
    assert m.validate_code("mcq_4") == "mcq_4"
    for bad in ("", "Bad", "-x", "a b"):
        with pytest.raises(m.Invalid):
            m.validate_code(bad)


def test_type_config():
    assert m.validate_type_config("single_choice", {"option_count": 4})["option_count"] == 4
    with pytest.raises(m.Invalid):
        m.validate_type_config("numeric", {"option_count": 4})
    with pytest.raises(m.Invalid):
        m.validate_type_config("single_choice", {"option_count": 1})
    with pytest.raises(m.Invalid):
        m.validate_type_config("bogus", {})


def test_descendants_and_cycles():
    tree = {"a": None, "b": "a", "c": "b", "d": None}
    assert set(m.descendants(tree, ["a"])) == {"a", "b", "c"}
    assert m.descendants(tree, ["d"]) == ["d"]
    assert m.creates_cycle(tree, "a", "c")
    assert not m.creates_cycle(tree, "d", "a")
    assert m.creates_cycle(tree, "a", "a")


def test_blueprint_sections():
    ok = m.validate_blueprint_sections([{"subject_id": U1, "count": 2, "weight": 1, "question_ids": [U1, U2]}])
    assert ok[0]["question_ids"] == [U1, U2]
    with pytest.raises(m.Invalid):
        m.validate_blueprint_sections([])
    with pytest.raises(m.Invalid):
        m.validate_blueprint_sections([{"subject_id": U1, "count": 3, "question_ids": [U1]}])
    with pytest.raises(m.Invalid):
        m.validate_blueprint_sections([{"subject_id": "nope", "count": 1}])


def test_lesson_selectors_and_visibility():
    assert m.validate_lesson_selectors({"topic_ids": [U1, U1]})["topic_ids"] == [U1]
    with pytest.raises(m.Invalid):
        m.validate_lesson_selectors({"question_count": 0})
    assert m.lesson_visible(30, 10, 30)
    assert not m.lesson_visible(29, 10, 30)
    assert not m.lesson_visible(40, 50, 30)


def test_validate_entity():
    d = m.validate_entity("blueprint", {"code": "x", "names": {"en": "X"}, "kind": "official", "duration_min": 90, "sections": [{"subject_id": U1, "count": 1}]})
    assert d["sections"][0]["weight"] == 1.0
    with pytest.raises(m.Invalid):
        m.validate_entity("blueprint", {"code": "x", "names": {"en": "X"}, "kind": "nope", "duration_min": 90, "sections": []})
    with pytest.raises(m.Invalid):
        m.validate_entity("path", {"language": "Russian!", "names": {"en": "p"}})


def test_permutation():
    assert m.sequence_is_permutation([1, 2], [2, 1])
    assert not m.sequence_is_permutation([1, 2], [1, 1])
    assert not m.sequence_is_permutation([1, 2], [1])
