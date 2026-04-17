from pydantic import BaseModel


class SolutionStep(BaseModel):
    """Model for step of a solution."""

    action: str # simple descriptor of the action
    formula: str | None = None # optional latex based math formula
    explanation: str | None = None # optional extended explanation
