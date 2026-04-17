from dataclasses import dataclass

from src.models.questions.subject import Subject


@dataclass
class SubjectConfig:
    """Configuration for a single subject's AI extraction pipeline."""

    subject: Subject
    prompt_template: str   # f-string with {categories} placeholder
    use_latex: bool        # True for MATH/PHYSICS; False for ENGLISH/HISTORY/etc.
