from enum import Enum


class Subject(Enum):
    """Subject types."""

    IQ = "IQ"
    MATH = "MATH"
    ENGLISH = "ENGLISH"
    GERMAN = "GERMAN"
    HISTORY = "HISTORY"
    PHYSICS = "PHYSICS"


# Score multiplier per subject: correct_ratio * 20 * SUBJECT_WEIGHTS[subject.value]
SUBJECT_WEIGHTS: dict[str, float] = {
    "IQ": 1.1,
    "MATH": 3.1,
    "ENGLISH": 3.1,
    "GERMAN": 3.1,
    "HISTORY": 3.1,
    "PHYSICS": 3.1,
}

# Human-readable names for bot UI
SUBJECT_DISPLAY: dict[str, str] = {
    "IQ": "IQ",
    "MATH": "Математика 🧮",
    "ENGLISH": "Английский 🇬🇧",
    "GERMAN": "Немецкий 🇩🇪",
    "HISTORY": "История 📜",
    "PHYSICS": "Физика ⚛️",
}