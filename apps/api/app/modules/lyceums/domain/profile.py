"""Lyceum profile rules: dormitory status, city codes, locale-keyed text. Pure."""

import re
from dataclasses import dataclass
from enum import StrEnum

from app.modules.lyceums.domain.rep import validate_description
from app.shared.errors import ValidationFailed

# Fields an approved representative may edit; everything else is admin-only.
REP_PROFILE_FIELDS = frozenset(
    {"description", "courses", "contacts", "dormitory_status", "dormitory_description"}
)

CITY_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,49}$")


@dataclass(frozen=True, slots=True)
class CityView:
    code: str
    names: dict[str, str]
    lyceum_count: int


class DormitoryStatus(StrEnum):
    AVAILABLE = "available"
    LIMITED = "limited"
    NONE = "none"
    UNKNOWN = "unknown"


def parse_dormitory_status(raw: str) -> DormitoryStatus:
    try:
        return DormitoryStatus(raw)
    except ValueError as e:
        raise ValidationFailed(
            f"unknown dormitory status: {raw}", code="invalid_dormitory_status"
        ) from e


def validate_dormitory_description(desc: dict[str, str]) -> dict[str, str]:
    """Same rules as the profile description: only the four locales, bounded length."""
    return validate_description(desc)


def normalize_city_code(code: str | None) -> str | None:
    """Blank clears the city; otherwise a lowercase slug. Existence is checked by the use case."""
    value = (code or "").strip().lower()
    if not value:
        return None
    if not CITY_CODE_RE.match(value):
        raise ValidationFailed("invalid city code", code="invalid_city")
    return value
