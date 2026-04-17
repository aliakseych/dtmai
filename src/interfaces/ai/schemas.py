from pydantic import BaseModel, field_validator

from src.models.questions.level import Level
from src.models.questions.solution_step import SolutionStep


class AIQuestionResponse(BaseModel):
    """Parsed and validated response from the AI extraction prompt."""

    category: str
    level: Level
    question_text: str
    answers: list[str]
    correct_answer: str
    solution_steps: list[SolutionStep] | None = None

    @field_validator("correct_answer")
    @classmethod
    def correct_answer_in_answers(cls, v: str, info) -> str:
        answers = info.data.get("answers", [])
        if answers and v not in answers:
            raise ValueError(
                f"correct_answer '{v}' must exactly match one of the answers: {answers}"
            )
        return v
