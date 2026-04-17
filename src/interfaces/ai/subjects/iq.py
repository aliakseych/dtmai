from src.interfaces.ai.subjects.base import SubjectConfig
from src.models.questions.subject import Subject

# Stub — implement when IQ question images are available
IQ_CONFIG = SubjectConfig(
    subject=Subject.IQ,
    prompt_template="",  # TODO: write IQ prompt
    use_latex=False,
)
