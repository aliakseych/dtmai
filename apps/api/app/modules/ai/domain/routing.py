"""Task tiers: each AI task maps to one or more model routes (slots) stored in the DB."""

from dataclasses import dataclass
from enum import StrEnum


class Task(StrEnum):
    EXTRACT = "extract"
    SOLVE = "solve"
    JUDGE = "judge"
    EXPLAIN = "explain"
    TUTOR = "tutor"
    GENERATE = "generate"


@dataclass(frozen=True, slots=True)
class ModelRoute:
    task: Task
    slot: int  # solve uses every enabled slot (independent solvers); other tasks use slot 0
    model: str
    temperature: float
    max_tokens: int
    price_in_micro_per_mtok: int  # micro-USD per 1M input tokens
    price_out_micro_per_mtok: int
    enabled: bool = True
