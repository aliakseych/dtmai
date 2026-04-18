import re

from src.controllers.bot.routers.user.bank.keyboard import list as list_kb
from src.controllers.bot.routers.user.bank.keyboard.list import PAGE_SIZE
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.types import InlineKeyboardMarkup

_LEVEL_ICON = {
    "ORIGINAL": "⭐",
    "HARD":     "🔴",
    "MEDIUM":   "🟡",
    "EASY":     "🟢",
}

_LATEX_RE = re.compile(r'\$[^$]+\$|\\\(.*?\\\)|\\\[.*?\\\]', re.DOTALL)


def _preview(question_text: str, length: int = 80) -> str:
    text = _LATEX_RE.sub('[формула]', question_text)
    text = text.replace('\n', ' ').strip()
    if len(text) > length:
        text = text[:length].rstrip() + '…'
    return text


def build_list_content(
    questions: list[dict],
    page: int,
    subject: str,
) -> tuple[str, InlineKeyboardMarkup]:
    subj_name = SUBJECT_DISPLAY.get(subject, subject)
    total = len(questions)

    if not questions:
        text = f"📚 <b>Банк вопросов</b> — {subj_name}\n\nВопросов по выбранным фильтрам не найдено."
        keyboard = list_kb.get(questions_page=[], total=0, page=0)
        return text, keyboard

    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_qs = questions[start:end]

    lines = [f"📚 <b>Банк вопросов</b> — {subj_name} ({total} вопр.)\n"]
    for i, q in enumerate(page_qs, start + 1):
        solved_mark = "✅" if q["solved"] else "○"
        level_icon = _LEVEL_ICON.get(q["level"], "")
        preview = _preview(q["question"])
        lines.append(f"{i}. {solved_mark} {level_icon} {preview}")

    keyboard = list_kb.get(questions_page=page_qs, total=total, page=page)
    return "\n".join(lines), keyboard