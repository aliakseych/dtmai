from enum import Enum


class Level(Enum):
    """Question level."""

    ORIGINAL = "ORIGINAL" # from a real exam
    HARD = "HARD" # harder than usual
    MEDIUM = "MEDIUM" # middle
    EASY = "EASY" # covering basic topics
