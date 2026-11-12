"""Admission plan (seats per direction) and contact rules, plus applicants-per-seat ratios."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from app.modules.lyceums.domain.models import competition_ratio
from app.shared.errors import ValidationFailed

SOURCE_SEED = "seed"
SOURCE_ADMIN = "admin"
MAX_PHONES = 8
MAX_SEATS = 100_000


@dataclass(frozen=True, slots=True)
class Seats:
    uz: int = 0
    ru: int = 0
    qq: int = 0

    @property
    def total(self) -> int:
        return self.uz + self.ru + self.qq


@dataclass(frozen=True, slots=True)
class PlanRow:
    """Seats of one direction (optionally one foreign language) at one lyceum and year."""

    lyceum_id: UUID
    year: int
    direction_code: str
    language_name: str | None
    seats: Seats
    source: str = SOURCE_SEED


@dataclass(frozen=True, slots=True)
class ContactCard:
    lyceum_id: UUID
    phones: tuple[str, ...]
    telegram: str | None
    source: str = SOURCE_SEED


def validate_seats(uz: int, ru: int, qq: int) -> Seats:
    for value in (uz, ru, qq):
        if value < 0 or value > MAX_SEATS:
            raise ValidationFailed("seats out of range", code="invalid_seats")
    return Seats(uz=uz, ru=ru, qq=qq)


def normalize_direction_code(code: str) -> str:
    code = code.strip()
    if not re.fullmatch(r"\d{4,20}", code):
        raise ValidationFailed("direction code must be digits", code="invalid_direction_code")
    return code


def normalize_language_name(name: str | None) -> str | None:
    name = (name or "").strip().lower()
    if len(name) > 40:
        raise ValidationFailed("language name too long", code="invalid_language_name")
    return name or None


def normalize_phone(raw: str) -> str | None:
    """`+998XXXXXXXXX` for a 9-digit (or 998-prefixed 12-digit) number, else None."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 12 and digits.startswith("998"):
        digits = digits[3:]
    return f"+998{digits}" if len(digits) == 9 else None


def normalize_telegram(raw: str | None) -> str | None:
    """Canonical `https://t.me/<handle>` link; None for blank input."""
    value = (raw or "").strip()
    if not value:
        return None
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^(t\.me|telegram\.me)/", "", value)
    value = value.lstrip("@")
    if not re.fullmatch(r"\+?[A-Za-z0-9_]{3,64}", value):
        raise ValidationFailed("invalid telegram handle", code="invalid_telegram")
    return f"https://t.me/{value}"


def validate_phones(raw: Iterable[str]) -> tuple[str, ...]:
    phones: list[str] = []
    for item in raw:
        phone = normalize_phone(item)
        if phone is None:
            raise ValidationFailed(f"invalid phone: {item}", code="invalid_phone")
        if phone not in phones:
            phones.append(phone)
    if len(phones) > MAX_PHONES:
        raise ValidationFailed("too many phones", code="too_many_phones")
    return tuple(phones)


@dataclass(frozen=True, slots=True)
class DirectionRatio:
    direction_code: str
    seats: int
    applications: int | None
    ratio: float | None


@dataclass(frozen=True, slots=True)
class AdmissionCompetition:
    """Applicants per seat: per direction where edu.uz data has the code, else per lyceum."""

    directions: tuple[DirectionRatio, ...]
    lyceum_ratio: float | None
    applications_year: int | None


def admission_competition(
    plan: Iterable[PlanRow], stats: Iterable[tuple[int, str, int]]
) -> AdmissionCompetition:
    """`stats` rows are (year, speciality_code, applications); the latest year is used.

    Direction ratio needs seats > 0 and at least one stat row with the same code. The lyceum
    ratio is all applications of that year over all planned seats.
    """
    seats_by_code: dict[str, int] = {}
    for row in plan:
        seats_by_code[row.direction_code] = (
            seats_by_code.get(row.direction_code, 0) + row.seats.total
        )
    rows = list(stats)
    year = max((y for y, _c, _a in rows), default=None)
    apps_by_code: dict[str, int] = {}
    for y, code, apps in rows:
        if y == year:
            apps_by_code[code] = apps_by_code.get(code, 0) + apps
    directions = tuple(
        DirectionRatio(
            direction_code=code,
            seats=seats,
            applications=apps_by_code.get(code),
            ratio=(competition_ratio(apps_by_code[code], seats) if code in apps_by_code else None),
        )
        for code, seats in sorted(seats_by_code.items())
    )
    total_seats = sum(seats_by_code.values())
    lyceum_ratio = (
        competition_ratio(sum(apps_by_code.values()), total_seats) if apps_by_code else None
    )
    return AdmissionCompetition(
        directions=directions, lyceum_ratio=lyceum_ratio, applications_year=year
    )


@dataclass(frozen=True, slots=True)
class SeedDirection:
    direction_code: str
    language_name: str | None
    seats: Seats


@dataclass(frozen=True, slots=True)
class SeedPlanEntry:
    """One lyceum of the admission-plan order, identified by its order number `ref`."""

    ref: int
    name: str
    directions: tuple[SeedDirection, ...]


@dataclass(frozen=True, slots=True)
class SeedContactEntry:
    ref: int
    name: str
    district: str
    phones: tuple[str, ...]
    telegram: str | None


KIND_PLAN = "plan"
KIND_CONTACT = "contact"
MATCH_AUTO = "auto"
MATCH_ADMIN = "admin"
