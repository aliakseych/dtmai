"""gamification: proper uz-Latn apostrophes and real uz-Cyrl quest/achievement titles

Revision ID: gamification_0003
Revises: gamification_0002
Create Date: 2026-11-14
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "gamification_0003"
down_revision = "gamification_0002"
branch_labels = None
depends_on = None

S = "gamification"


def _t(latn: str, cyrl: str, ru: str, en: str) -> str:
    return json.dumps({"uz-Latn": latn, "uz-Cyrl": cyrl, "ru": ru, "en": en}, ensure_ascii=False)


QUESTS = {
    "earn_50_xp": _t("50 XP to‘plang", "50 XP тўпланг", "Заработайте 50 XP", "Earn 50 XP"),
    "earn_100_xp": _t("100 XP to‘plang", "100 XP тўпланг", "Заработайте 100 XP", "Earn 100 XP"),
    "complete_1_lesson": _t(
        "1 ta dars tugating", "1 та дарс тугатинг", "Пройдите 1 урок", "Complete 1 lesson"
    ),
    "complete_3_lessons": _t(
        "3 ta dars tugating", "3 та дарс тугатинг", "Пройдите 3 урока", "Complete 3 lessons"
    ),
    "correct_15": _t(
        "15 ta to‘g‘ri javob",
        "15 та тўғри жавоб",
        "15 правильных ответов",
        "Get 15 answers right",
    ),
    "perfect_session": _t(
        "Xatosiz dars", "Хатосиз дарс", "Урок без ошибок", "Finish a lesson with no mistakes"
    ),
    "review_session": _t(
        "Xatolar ustida ishlang",
        "Хатолар устида ишланг",
        "Повторите ошибки",
        "Review your mistakes",
    ),
}

ACHIEVEMENTS = {
    "streak_7": _t("7 kunlik seriya", "7 кунлик серия", "Серия 7 дней", "7-day streak"),
    "streak_30": _t("30 kunlik seriya", "30 кунлик серия", "Серия 30 дней", "30-day streak"),
    "xp_1000": _t("1000 XP", "1000 XP", "1000 XP", "1000 XP"),
    "xp_10000": _t("10 000 XP", "10 000 XP", "10 000 XP", "10,000 XP"),
    "lessons_10": _t("10 ta dars", "10 та дарс", "10 уроков", "10 lessons"),
    "correct_500": _t(
        "500 ta to‘g‘ri javob",
        "500 та тўғри жавоб",
        "500 правильных ответов",
        "500 correct answers",
    ),
    "first_mock": _t("Birinchi mock", "Биринчи мок", "Первый пробный экзамен", "First mock exam"),
}


def upgrade() -> None:
    bind = op.get_bind()
    for table, rows in (("quest_templates", QUESTS), ("achievement_defs", ACHIEVEMENTS)):
        for code, title in rows.items():
            bind.execute(
                sa.text(f"UPDATE {S}.{table} SET title = CAST(:t AS JSON) WHERE code = :c"),
                {"t": title, "c": code},
            )


def downgrade() -> None:
    """Data-only fix; the previous titles are not restored."""
