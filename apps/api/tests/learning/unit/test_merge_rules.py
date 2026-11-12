from app.modules.learning.domain.merge import (
    merge_mastery,
    merge_rating,
    src_card_wins,
    src_placement_wins,
)


def test_rating_keeps_higher():
    assert merge_rating(1100, 1300) == 1300


def test_mastery_sums_and_weights():
    score, att, cor = merge_mastery((0.5, 10, 5), (1.0, 10, 10))
    assert (att, cor) == (20, 15) and abs(score - 0.75) < 1e-9
    assert merge_mastery((0.2, 0, 0), (0.6, 0, 0))[0] == 0.6


def test_card_and_placement_pick():
    assert src_card_wins(1, 3) and not src_card_wins(3, 3)
    assert src_placement_wins(True, False)
    assert not src_placement_wins(False, True) and not src_placement_wins(False, False)
