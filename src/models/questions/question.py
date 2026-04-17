from datetime import datetime

from pydantic import BaseModel

from src.models.questions.level import Level
from src.models.questions.solution_step import SolutionStep
from src.models.questions.subject import Subject


class Question(BaseModel):
    """Question model."""

    id: str  # uuid v7

    subject: Subject  # subject this question belongs to
    category_id: str  # uuid v7 link to category
    source_id: str | None = None # optional uuid v7 link to source

    level: Level
    question: str # question text

    answers: list[str]
    correct_answer: str

    image_url: str | None = None  # hosted URL of the source image, shown in the bot

    solution_steps: list[SolutionStep] | None = None # optional solutions steps

    created_at: datetime
    updated_at: datetime
