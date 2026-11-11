from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev

MIN_ATTEMPTS = 3
WINDOW = 10
SD_FLOOR = 0.1  # never claim tighter than 10% of the scale
Z = 1.96


@dataclass(frozen=True, slots=True)
class Prediction:
    value: float
    low: float
    high: float
    attempts: int
    confident: bool


def predict(history: list[tuple[float, float]], *, min_attempts: int = MIN_ATTEMPTS) -> Prediction | None:
    """history: (score, max_score) newest first. Returns None with no data.

    Works on the normalized scale then maps onto the newest attempt's maximum.
    """
    if not history:
        return None
    recent = history[:WINDOW]
    ratios = [s / m for s, m in recent if m > 0]
    if not ratios:
        return None
    n = len(ratios)
    mu = mean(ratios)
    half = Z * max(pstdev(ratios), SD_FLOOR) / sqrt(n)
    scale = recent[0][1]
    return Prediction(
        round(mu * scale, 2),
        round(max(0.0, mu - half) * scale, 2),
        round(min(1.0, mu + half) * scale, 2),
        n,
        n >= min_attempts,
    )
