from app.modules.labeling.domain.autogen import plan_autogen


def test_scales_by_per_question():
    assert plan_autogen({"a": 3}, 2, 60) == [("a", 6)]


def test_cap_truncates_and_drops_rest():
    assert plan_autogen({"a": 5, "b": 4, "c": 1}, 2, 12) == [("a", 10), ("b", 2)]


def test_zero_disables():
    assert plan_autogen({"a": 3}, 0, 60) == []
    assert plan_autogen({"a": 3}, 2, 0) == []


def test_largest_first_and_skips_empty():
    assert plan_autogen({"a": 1, "b": 3, "c": 0}, 1, 100) == [("b", 3), ("a", 1)]
