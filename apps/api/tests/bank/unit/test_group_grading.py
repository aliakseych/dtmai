from app.modules.bank.domain.kinds import grade_group

OPTS = {"options": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]}
CHILDREN = [
    ("c1", "single_choice", OPTS, {"choice": "a"}),
    ("c2", "numeric", {}, {"value": 4}),
]


def test_group_all_correct():
    g, correct = grade_group(CHILDREN, {"answers": {"c1": {"choice": "a"}, "c2": {"value": "4"}}})
    assert g.correct and g.score == 1.0
    assert correct == {"answers": {"c1": {"choice": "a"}, "c2": {"value": 4}}}


def test_group_partial_and_missing_child():
    g, _ = grade_group(CHILDREN, {"answers": {"c1": {"choice": "a"}, "c2": {"value": 5}}})
    assert not g.correct and g.score == 0.5
    g, _ = grade_group(CHILDREN, {"answers": {"c1": {"choice": "a"}}})
    assert not g.correct and g.score == 0.5


def test_group_malformed_response():
    for bad in ({}, {"answers": "x"}, "x", None):
        g, correct = grade_group(CHILDREN, bad)
        assert not g.correct and g.score == 0.0
        assert set(correct["answers"]) == {"c1", "c2"}


def test_group_without_children_is_wrong():
    assert not grade_group([], {"answers": {}})[0].correct
