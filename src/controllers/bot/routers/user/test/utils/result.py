from collections import defaultdict

from src.models.questions.subject import SUBJECT_DISPLAY, SUBJECT_WEIGHTS


def aggregate_results(questions: list[dict], answered: dict) -> dict:
    """
    Compute per-subject and per-category stats from a completed test.
    Returns subject_correct, subject_total, category_correct, category_total,
    total_correct, total_q, projected.
    """
    subject_correct: dict[str, int] = defaultdict(int)
    subject_total: dict[str, int] = defaultdict(int)
    category_correct: dict[str, int] = defaultdict(int)
    category_total: dict[str, int] = defaultdict(int)

    for q in questions:
        result = answered.get(q["id"])
        if result is None:
            continue
        subj = result["subject"]
        cat = q.get("category_id", "")
        subject_total[subj] += 1
        category_total[cat] += 1
        if result["is_correct"]:
            subject_correct[subj] += 1
            category_correct[cat] += 1

    projected = sum(
        (subject_correct[subj] / total) * 20 * SUBJECT_WEIGHTS.get(subj, 3.1)
        for subj, total in subject_total.items() if total > 0
    )

    return {
        "subject_correct": dict(subject_correct),
        "subject_total": dict(subject_total),
        "category_correct": dict(category_correct),
        "category_total": dict(category_total),
        "total_correct": sum(subject_correct.values()),
        "total_q": sum(subject_total.values()),
        "projected": projected,
    }


def build_part_result_text(subject: str, stats: dict, cat_names: dict[str, str]) -> str:
    """Intermediate result shown after finishing one subject part."""
    correct = stats["subject_correct"].get(subject, 0)
    total = stats["subject_total"].get(subject, 0)
    display = SUBJECT_DISPLAY.get(subject, subject)

    lines = [
        f"✅ <b>{display} — итог части</b>\n",
        f"Правильно: <b>{correct}/{total}</b> ({_pct(correct, total)}%)\n",
        "По категориям:",
    ]
    for cat_id, cat_total in sorted(stats["category_total"].items(), key=lambda x: -x[1]):
        cat_correct = stats["category_correct"].get(cat_id, 0)
        name = cat_names.get(cat_id, cat_id[:8] + "…")
        lines.append(f"  • {name}: {cat_correct}/{cat_total}")

    return "\n".join(lines)


def build_result_text(stats: dict, cat_names: dict[str, str]) -> str:
    total_correct = stats["total_correct"]
    total_q = stats["total_q"]
    projected = stats["projected"]

    lines = [
        "📊 <b>Результаты теста</b>\n",
        f"Итого: <b>{total_correct}/{total_q}</b> ({_pct(total_correct, total_q)}%)\n",
    ]
    for subj, total in stats["subject_total"].items():
        correct = stats["subject_correct"].get(subj, 0)
        lines.append(f"{SUBJECT_DISPLAY.get(subj, subj)}: <b>{correct}/{total}</b> ({_pct(correct, total)}%)")

    lines.append(f"\n🎯 Прогноз баллов: <b>{projected:.1f}</b>")
    lines.append("<i>(сумма по предметам: верно% × 20 × коэффициент)</i>\n")

    lines.append("По категориям:")
    for cat_id, total in sorted(stats["category_total"].items(), key=lambda x: -x[1]):
        correct = stats["category_correct"].get(cat_id, 0)
        name = cat_names.get(cat_id, cat_id[:8] + "…")
        lines.append(f"  • {name}: {correct}/{total}")

    return "\n".join(lines)


def _pct(correct: int, total: int) -> int:
    return round(correct / total * 100) if total else 0