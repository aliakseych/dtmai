from datetime import datetime

from pydantic import BaseModel


class QuestionAttempt(BaseModel):
    """Records a single user answer to a question."""

    id: str  # uuid v7

    user_id: str      # uuid v7
    question_id: str  # uuid v7
    set_id: str | None = None  # uuid v7 — present when attempted as part of a set

    selected_answer: str
    is_correct: bool

    answered_at: datetime
    time_taken_ms: int | None = None  # client-reported, optional
