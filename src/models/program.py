from pydantic import BaseModel


class Program(BaseModel):
    """
    A named collection of subjects forming a test program.
    Added manually via DB. Subjects reference Subject enum values.
    Example: {"name": "Точные науки", "subjects": ["MATH", "ENGLISH", "IQ"]}
    """

    id: str        # uuid v7
    name: str      # e.g. "Точные науки", "Экономика"
    subjects: list[str]  # ordered list of Subject.value strings