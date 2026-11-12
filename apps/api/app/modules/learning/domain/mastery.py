"""Mastery per (topic, question type): an EMA of correctness, damped by attempt count."""

from dataclasses import dataclass

MIN_ATTEMPTS = 3
WEAK_BELOW = 0.6
MIN_ALPHA = 0.15


@dataclass(slots=True)
class Mastery:
    score: float = 0.5
    attempts: int = 0
    correct: int = 0

    def record(self, correct: bool) -> None:
        alpha = max(1 / (self.attempts + 2), MIN_ALPHA)
        self.score += alpha * ((1.0 if correct else 0.0) - self.score)
        self.attempts += 1
        self.correct += 1 if correct else 0

    @property
    def is_weak(self) -> bool:
        return self.attempts >= MIN_ATTEMPTS and self.score < WEAK_BELOW


def weakest(items: list[tuple[object, Mastery]], limit: int) -> list[tuple[object, Mastery]]:
    """Weak areas first (lowest score), ties by more attempts."""
    weak = [i for i in items if i[1].is_weak]
    return sorted(weak, key=lambda i: (i[1].score, -i[1].attempts))[:limit]
