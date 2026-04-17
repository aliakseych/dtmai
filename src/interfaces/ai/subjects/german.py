from src.interfaces.ai.subjects.base import SubjectConfig
from src.models.questions.subject import Subject

# Stub — implement when German exam data is available
GERMAN_CONFIG = SubjectConfig(
    subject=Subject.GERMAN,
    prompt_template="",  # TODO: write German prompt (adapt from English)
    use_latex=False,
)
