from src.interfaces.ai.subjects.base import SubjectConfig
from src.interfaces.ai.subjects.english import ENGLISH_CONFIG
from src.interfaces.ai.subjects.math import MATH_CONFIG
from src.models.questions.subject import Subject

# Registry: add new subjects here — no other changes needed
SUBJECT_CONFIGS: dict[Subject, SubjectConfig] = {
    Subject.MATH: MATH_CONFIG,
    Subject.ENGLISH: ENGLISH_CONFIG,
}


def get_config(subject: Subject) -> SubjectConfig:
    config = SUBJECT_CONFIGS.get(subject)
    if config is None:
        raise ValueError(f"No AI config registered for subject: {subject}")
    return config
