from collections import defaultdict

from src.models.questions.subject import SUBJECT_DISPLAY, SUBJECT_WEIGHTS


def aggregate_attempts(attempts: list[dict]) -> dict:
    """
    Aggregate attempt history into per-subject accuracy and projected score.
    Returns subject_correct, subject_total, total_correct, total_q, unique_q, projected.
    """
    subject_correct: dict[str, int] = defaultdict(int)
    subject_total: dict[str, int] = defaultdict(int)

    for attempt in attempts:
        subj = attempt.get("subject", "")
        if not subj:
            continue
        subject_total[subj] += 1
        if attempt.get("is_correct"):
            subject_correct[subj] += 1

    projected = sum(
        (subject_correct[subj] / total) * 20 * SUBJECT_WEIGHTS.get(subj, 3.1)
        for subj, total in subject_total.items() if total > 0
    )

    return {
        "subject_correct": dict(subject_correct),
        "subject_total": dict(subject_total),
        "total_correct": sum(subject_correct.values()),
        "total_q": sum(subject_total.values()),
        "unique_q": len({a["question_id"] for a in attempts}),
        "projected": projected,
    }


def build_stats_text(data: dict) -> str:
    total_correct = data["total_correct"]
    total_q = data["total_q"]
    unique_q = data["unique_q"]

    lines = [
        "📊 <b>Статистика</b>\n",
        f"Всего ответов: <b>{total_q}</b> ({unique_q} уникальных вопросов)",
        f"Правильно: <b>{total_correct}</b> ({_pct(total_correct, total_q)}%)\n",
    ]
    for subj, total in sorted(data["subject_total"].items(), key=lambda x: -x[1]):
        correct = data["subject_correct"].get(subj, 0)
        lines.append(f"{SUBJECT_DISPLAY.get(subj, subj)}: <b>{correct}/{total}</b> ({_pct(correct, total)}%)")

    lines.append(f"\n🎯 Прогноз баллов: <b>{data['projected']:.1f}</b>")
    lines.append("<i>(верно% × 20 × коэффициент по каждому предмету)</i>")

    return "\n".join(lines)


def _pct(correct: int, total: int) -> int:
    return round(correct / total * 100) if total else 0