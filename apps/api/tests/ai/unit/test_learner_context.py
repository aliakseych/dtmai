from app.modules.ai.application.learner_context import LearnerProfile, render_learner_context
from app.modules.ai.application.tutor import SYSTEM


def test_context_contains_track_subjects_weak_topics_lyceum_locale() -> None:
    out = render_learner_context(
        LearnerProfile(
            "uz-Latn",
            "Aniq fanlar-1",
            ("Matematika", "Fizika"),
            ("Kasrlar", "Tenglamalar"),
            ("Akademik litsey",),
        )
    )
    for needle in (
        "uz-Latn",
        "Aniq fanlar-1",
        "Matematika, Fizika",
        "Kasrlar, Tenglamalar",
        "Akademik litsey",
    ):
        assert needle in out


def test_context_empty_when_nothing_known() -> None:
    assert render_learner_context(LearnerProfile("ru", None, (), (), ())) == ""


def test_system_prompt_demands_typographic_apostrophes() -> None:
    assert "\u2018" in SYSTEM and "\u02bc" in SYSTEM
