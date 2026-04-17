from pydantic import BaseModel


class Category(BaseModel):
    """Question type."""

    id: str # uuid v7

    subject_id: str # link to subject

    name: str # like "Linear functions" / "Surds"
