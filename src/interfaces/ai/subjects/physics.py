from src.interfaces.ai.subjects.base import SubjectConfig
from src.models.questions.subject import Subject

# Stub — implement when Physics exam data is available
PHYSICS_CONFIG = SubjectConfig(
    subject=Subject.PHYSICS,
    prompt_template="",  # TODO: write Physics prompt (adapt from Math, use_latex=True)
    use_latex=True,
)
