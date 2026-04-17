from datetime import datetime

from pydantic import BaseModel

from src.models.questions.question import Question


class QuestionSet(BaseModel):
    """Set of questions."""

    id: str # uuid v7

    name: str # name of the set
    description: str | None = None

    subjects_ids: list[str] # uuids, in order they will be shown on the test
    questions_by_subject: dict[str, list[Question]] # uuid of subject & it's questions

    created_at: datetime
    updated_at: datetime
