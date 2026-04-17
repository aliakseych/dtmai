from src.interfaces.ai.subjects.base import SubjectConfig
from src.models.questions.subject import Subject

# Stub — implement when History exam data is available
HISTORY_CONFIG = SubjectConfig(
    subject=Subject.HISTORY,
    prompt_template="",  # TODO: write History prompt
    use_latex=False,
)
