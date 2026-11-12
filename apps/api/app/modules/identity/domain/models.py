from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from app.shared.errors import Conflict, ValidationFailed

LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
DEFAULT_LOCALE = "uz-Latn"
MIN_PASSWORD_LENGTH = 8
MAX_SUBJECTS = 10
MAX_FIELD_CODE_LENGTH = 20
MAX_DREAM_LYCEUMS = 3
MAX_CITY_LENGTH = 50
GUEST_RETENTION_DAYS = 30


class Role(StrEnum):
    GUEST = "guest"
    STUDENT = "student"
    EDITOR = "editor"
    LYCEUM_REP = "lyceum_rep"
    ADMIN = "admin"
    LABELER = "labeler"


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValidationFailed("invalid email", code="invalid_email")
    return value


def validate_locale(locale: str) -> str:
    if locale not in LOCALES:
        raise ValidationFailed(f"unsupported locale: {locale}", code="invalid_locale")
    return locale


def validate_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationFailed("password too short", code="weak_password")
    return password


def validate_city(city: str | None) -> str | None:
    """Blank clears the city; otherwise a trimmed city code (existence is checked by the service)."""
    if city is None:
        return None
    value = city.strip()
    if len(value) > MAX_CITY_LENGTH:
        raise ValidationFailed("city too long", code="invalid_city")
    return value or None


def validate_field_code(code: str | None) -> str | None:
    """Blank clears the field; otherwise a trimmed speciality code."""
    value = (code or "").strip()
    if len(value) > MAX_FIELD_CODE_LENGTH:
        raise ValidationFailed("field code too long", code="invalid_field_code")
    return value or None


def dream_field_mismatch(
    field_code: str | None, dream_lyceum_ids: list[UUID], offered: Mapping[UUID, set[str]]
) -> list[UUID]:
    """Dream lyceums that do not offer the chosen field (never rejects; priority order kept)."""
    if field_code is None:
        return []
    return [i for i in dream_lyceum_ids if field_code not in offered.get(i, set())]


def validate_subject_ids(ids: list[UUID]) -> list[UUID]:
    """Order-preserving dedupe; bounded."""
    unique = list(dict.fromkeys(ids))
    if len(unique) > MAX_SUBJECTS:
        raise ValidationFailed("too many subjects", code="too_many_subjects")
    return unique


def validate_dream_lyceum_ids(ids: list[UUID]) -> list[UUID]:
    """Ordered priority list (position 1 = first choice): at most 3, no repeats."""
    if len(ids) > MAX_DREAM_LYCEUMS:
        raise ValidationFailed("at most 3 dream lyceums", code="too_many_dream_lyceums")
    if len(set(ids)) != len(ids):
        raise ValidationFailed("duplicate dream lyceum", code="duplicate_dream_lyceum")
    return list(ids)


def is_guest_expired(
    roles: set[Role],
    last_seen_at: datetime | None,
    *,
    now: datetime,
    retention_days: int = GUEST_RETENTION_DAYS,
) -> bool:
    """A pure guest (no other role) unseen for more than `retention_days`."""
    if roles != {Role.GUEST} or last_seen_at is None:
        return False
    return now - last_seen_at > timedelta(days=retention_days)


def guest_cutoff(now: datetime, retention_days: int = GUEST_RETENTION_DAYS) -> datetime:
    return now - timedelta(days=retention_days)


def locale_from_telegram(language_code: str | None) -> str:
    code = (language_code or "").lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    return DEFAULT_LOCALE


@dataclass(slots=True)
class User:
    id: UUID
    name: str
    locale: str = DEFAULT_LOCALE
    email: str | None = None
    email_verified: bool = False
    password_hash: str | None = None
    telegram_id: int | None = None
    roles: set[Role] = field(default_factory=lambda: {Role.STUDENT})
    dream_lyceum_ids: list[UUID] = field(default_factory=list)
    education_language_id: UUID | None = None
    city: str | None = None
    field_code: str | None = None
    subject_ids: list[UUID] = field(default_factory=list)
    created_at: datetime | None = None
    last_seen_at: datetime | None = None
    telegram_username: str | None = None
    disabled: bool = False
    is_system: bool = False

    def __post_init__(self) -> None:
        if not self.email and self.telegram_id is None and Role.GUEST not in self.roles:
            raise ValidationFailed("user needs an email or a telegram id", code="no_identity")
        validate_locale(self.locale)

    @property
    def target_lyceum_id(self) -> UUID | None:
        """The first-priority dream lyceum (what leaderboards and comparisons use)."""
        return self.dream_lyceum_ids[0] if self.dream_lyceum_ids else None

    def rename(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationFailed("name is empty", code="invalid_name")
        self.name = name


def adopt_guest_profile(target: User, guest: User) -> None:
    """Fill the target's empty onboarding/profile fields from a guest that is being merged into it."""
    if not target.dream_lyceum_ids and guest.dream_lyceum_ids:
        target.dream_lyceum_ids = list(guest.dream_lyceum_ids)
    if target.education_language_id is None:
        target.education_language_id = guest.education_language_id
    if target.city is None:
        target.city = guest.city
    if target.field_code is None:
        target.field_code = guest.field_code
    if not target.subject_ids and guest.subject_ids:
        target.subject_ids = list(guest.subject_ids)


def parse_role_set(raw: list[str]) -> set[Role]:
    """Validate a role list. Pure."""
    roles: set[Role] = set()
    for value in raw:
        try:
            roles.add(Role(value))
        except ValueError as e:
            raise ValidationFailed(f"unknown role: {value}", code="invalid_role") from e
    if not roles:
        raise ValidationFailed("at least one role is required", code="invalid_role")
    if Role.GUEST in roles and len(roles) > 1:
        raise ValidationFailed("guest cannot be combined with other roles", code="invalid_role")
    return roles


def parse_roles(raw: list[str], *, actor_id: UUID, target_id: UUID) -> set[Role]:
    """Validate a role assignment coming from an admin. Pure."""
    roles = parse_role_set(raw)
    if actor_id == target_id and Role.ADMIN not in roles:
        raise ValidationFailed("admins cannot remove their own admin role", code="self_demotion")
    return roles


def ensure_admin_change_allowed(
    *, actor_id: UUID, target: User, new_roles: set[Role], disabled: bool, active_admins: int
) -> None:
    """Superadmin protection. Pure.

    An admin cannot disable themselves, and the last active admin can be neither demoted nor disabled.
    """
    if actor_id == target.id and disabled and not target.disabled:
        raise ValidationFailed("admins cannot disable themselves", code="self_disable")
    was_active_admin = Role.ADMIN in target.roles and not target.disabled
    still_active_admin = Role.ADMIN in new_roles and not disabled
    if was_active_admin and not still_active_admin and active_admins <= 1:
        raise Conflict("the last admin cannot be demoted or disabled", code="last_admin")


@dataclass(frozen=True, slots=True)
class EmailCode:
    id: UUID
    user_id: UUID
    code_hash: str
    expires_at: datetime
    attempts: int = 0
    consumed: bool = False


@dataclass(frozen=True, slots=True)
class RefreshToken:
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked: bool = False
