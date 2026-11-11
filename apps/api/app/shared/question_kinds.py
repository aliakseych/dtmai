"""Closed, versioned set of question kinds. Adding a kind requires code (validation + grading)."""

KINDS_VERSION = 1

SINGLE_CHOICE = "single_choice"
MULTI_CHOICE = "multi_choice"
NUMERIC = "numeric"
SHORT_TEXT = "short_text"
MATCHING = "matching"
ORDERING = "ordering"
PASSAGE_GROUP = "passage_group"

QUESTION_KINDS: tuple[str, ...] = (
    SINGLE_CHOICE,
    MULTI_CHOICE,
    NUMERIC,
    SHORT_TEXT,
    MATCHING,
    ORDERING,
    PASSAGE_GROUP,
)
