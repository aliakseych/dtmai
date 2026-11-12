from datetime import date
from uuid import uuid4

from app.modules.gamification.domain.quests import QuestProgress, QuestTemplate, pick_templates
from app.modules.gamification.domain.xp import XpCaps, clamp_session_xp, within_daily_cap

CAPS = XpCaps(daily_cap=600, session_cap=150, per_item_cap=10)


def test_session_xp_clamped_by_items_and_cap() -> None:
    assert clamp_session_xp(500, 5, CAPS) == 50
    assert clamp_session_xp(500, 100, CAPS) == 150
    assert clamp_session_xp(20, 5, CAPS) == 20
    assert clamp_session_xp(-5, 5, CAPS) == 0


def test_daily_cap() -> None:
    assert within_daily_cap(100, 550, 600) == 50
    assert within_daily_cap(100, 700, 600) == 0


def test_quest_picking_is_stable_per_day() -> None:
    ts = [QuestTemplate(uuid4(), f"q{i}", "xp_earned", 10, 1, 0) for i in range(8)]
    u = uuid4()
    d = date(2026, 1, 5)
    a = pick_templates(ts, u, d, 3)
    assert a == pick_templates(ts, u, d, 3) and len(a) == 3
    assert pick_templates(ts, u, d, 0) == []


def test_quest_progress_completes_once() -> None:
    q = QuestProgress(progress=0, target=3)
    assert not q.advance(2)
    assert q.advance(5) and q.progress == 3
    assert not q.advance(1)


def test_quest_action_maps_every_metric() -> None:
    from app.modules.gamification.domain.quests import METRICS, quest_action

    expected = {
        "lessons_completed": "lesson",
        "perfect_sessions": "lesson",
        "xp_earned": "lesson",
        "streak_kept": "lesson",
        "review_sessions": "review",
        "mocks_submitted": "mock",
        "correct_answers": "drill",
    }
    assert {m: quest_action(m) for m in METRICS} == expected
    assert quest_action("unknown") == "any"
