"""Fields of study (edu.uz specialities) and the subjects they require. Pure."""

from dataclasses import dataclass
from uuid import UUID

from app.shared.errors import ValidationFailed

MAX_FIELD_SUBJECTS = 10
MAX_SPECIALITY_CODE = 20


@dataclass(frozen=True, slots=True)
class FieldView:
    code: str
    name: str
    subject_ids: list[UUID]
    mapped: bool


def normalize_speciality_code(code: str) -> str:
    value = (code or "").strip()
    if not value or len(value) > MAX_SPECIALITY_CODE:
        raise ValidationFailed("invalid field code", code="invalid_field_code")
    return value


def validate_field_subject_ids(ids: list[UUID]) -> list[UUID]:
    """Order-preserving dedupe; bounded."""
    unique = list(dict.fromkeys(ids))
    if len(unique) > MAX_FIELD_SUBJECTS:
        raise ValidationFailed("too many subjects", code="too_many_subjects")
    return unique
