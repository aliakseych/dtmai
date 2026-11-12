"""Rules for folding a guest's learning rows into the signed-in account (nothing earned is lost)."""


def merge_rating(dst_elo: float, src_elo: float) -> float:
    return max(dst_elo, src_elo)


def merge_mastery(
    dst: tuple[float, int, int], src: tuple[float, int, int]
) -> tuple[float, int, int]:
    """(score, attempts, correct): counters add up, score is the attempt-weighted mean."""
    d_score, d_att, d_cor = dst
    s_score, s_att, s_cor = src
    total = d_att + s_att
    score = (d_score * d_att + s_score * s_att) / total if total else max(d_score, s_score)
    return score, total, d_cor + s_cor


def src_card_wins(dst_reps: int, src_reps: int) -> bool:
    """The card with more successful reviews carries more history; ties keep the target."""
    return src_reps > dst_reps


def src_placement_wins(dst_skipped: bool, src_skipped: bool) -> bool:
    """An earned placement beats a skipped one; otherwise the target stays."""
    return dst_skipped and not src_skipped
