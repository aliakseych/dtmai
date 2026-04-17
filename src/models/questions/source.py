from pydantic import BaseModel


class Source(BaseModel):
    """Model of question source."""

    id: str # uuid v7

    name: str
