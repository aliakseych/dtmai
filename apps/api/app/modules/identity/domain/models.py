from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.shared.errors import ValidationFailed

LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
DEFAULT_LOCALE = "uz-Latn"
MIN_PASSWORD_LENGTH = 8


class Role(StrEnum):
    GUEST = "guest"
    STUDENT = "student"
    EDITOR = "editor"
    ADMIN = "admin"


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
    target_lyceum_id: UUID | None = None
    education_language_id: UUID | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.email and self.telegram_id is None and Role.GUEST not in self.roles:
            raise ValidationFailed("user needs an email or a telegram id", code="no_identity")
        validate_locale(self.locale)

    def rename(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationFailed("name is empty", code="invalid_name")
        self.name = name


def parse_roles(raw: list[str], *, actor_id: UUID, target_id: UUID) -> set[Role]:
    """Validate a role assignment coming from an admin. Pure."""
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
    if actor_id == target_id and Role.ADMIN not in roles:
        raise ValidationFailed("admins cannot remove their own admin role", code="self_demotion")
    return roles


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
