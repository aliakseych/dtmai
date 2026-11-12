"""Lyceum representative rules: membership scoping and post moderation. Pure."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.modules.lyceums.domain.admission import normalize_telegram, validate_phones
from app.shared.errors import Conflict, Forbidden, ValidationFailed

LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
MAX_TITLE = 200
MAX_BODY = 5000
MAX_COURSES = 50
MAX_GALLERY = 20
MAX_COURSE_LEN = 200
EMAIL_RE = re.compile(r"[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s.]{2,}")
CONTACT_KEYS = ("phone", "telegram", "email")


class PostKind(StrEnum):
    ANNOUNCEMENT = "announcement"
    OFFER = "offer"
    FREE_MOCK = "free_mock"
    VISIT = "visit"
    EVENT = "event"
    ALUMNI = "alumni"
    CHAT_LINK = "chat_link"
    FACULTY = "faculty"


# Kinds that describe something happening at a time.
TIMED_KINDS = frozenset({PostKind.FREE_MOCK, PostKind.VISIT, PostKind.EVENT})
LINK_KINDS = frozenset({PostKind.CHAT_LINK})


class PostStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"


class MembershipStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REVOKED = "revoked"


def parse_kind(raw: str) -> PostKind:
    try:
        return PostKind(raw)
    except ValueError as e:
        raise ValidationFailed(f"unknown post kind: {raw}", code="invalid_post_kind") from e


def validate_link(link: str | None) -> str | None:
    if link is None or not link.strip():
        return None
    value = link.strip()
    if not value.startswith(("https://", "http://", "tg://")) or len(value) > 500:
        raise ValidationFailed("invalid link", code="invalid_link")
    return value


@dataclass(slots=True)
class RepMembership:
    user_id: UUID
    lyceum_id: UUID
    status: MembershipStatus = MembershipStatus.PENDING
    note: str | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None

    @classmethod
    def apply(
        cls, user_id: UUID, lyceum_id: UUID, note: str | None, *, is_guest: bool
    ) -> "RepMembership":
        if is_guest:
            raise Forbidden("sign in to apply", code="guest_cannot_apply")
        note = (note or "").strip()[:1000] or None
        return cls(user_id=user_id, lyceum_id=lyceum_id, note=note)

    def approve(self, now: datetime) -> None:
        if self.status is MembershipStatus.APPROVED:
            raise Conflict("already approved", code="rep_already_approved")
        self.status = MembershipStatus.APPROVED
        self.decided_at = now

    def revoke(self, now: datetime) -> None:
        if self.status is not MembershipStatus.APPROVED:
            raise Conflict("membership is not approved", code="rep_not_approved")
        self.status = MembershipStatus.REVOKED
        self.decided_at = now

    def ensure_manages(self, lyceum_id: UUID) -> None:
        """Rep content rights are scoped to one lyceum and require approval."""
        if self.lyceum_id != lyceum_id or self.status is not MembershipStatus.APPROVED:
            raise Forbidden("not a representative of this lyceum", code="rep_forbidden")


def ensure_can_apply(existing: RepMembership | None) -> None:
    if existing is None:
        return
    if existing.status is MembershipStatus.APPROVED:
        raise Conflict("already a representative", code="rep_already_approved")
    if existing.status is MembershipStatus.REVOKED:
        raise Conflict("representative access was revoked", code="rep_revoked")
    raise Conflict("application already pending", code="rep_application_pending")


@dataclass(slots=True)
class Post:
    id: UUID
    lyceum_id: UUID
    author_id: UUID
    kind: PostKind
    title: str
    body: str
    starts_at: datetime | None = None
    link: str | None = None
    status: PostStatus = PostStatus.PENDING
    reject_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.body = self.body.strip()
        self.link = validate_link(self.link)
        if not self.title or len(self.title) > MAX_TITLE:
            raise ValidationFailed("invalid title", code="invalid_post_title")
        if len(self.body) > MAX_BODY:
            raise ValidationFailed("body too long", code="invalid_post_body")
        if self.kind in TIMED_KINDS and self.starts_at is None:
            raise ValidationFailed("starts_at is required for this kind", code="starts_at_required")
        if self.kind in LINK_KINDS and self.link is None:
            raise ValidationFailed("link is required for this kind", code="link_required")

    def rep_edit(
        self, *, kind: PostKind, title: str, body: str, starts_at: datetime | None, link: str | None
    ) -> None:
        """Any rep edit re-enters moderation (published content never changes unreviewed)."""
        if self.status is PostStatus.DRAFT:
            raise Conflict("draft posts are not editable", code="post_state")
        candidate = Post(
            id=self.id,
            lyceum_id=self.lyceum_id,
            author_id=self.author_id,
            kind=kind,
            title=title,
            body=body,
            starts_at=starts_at,
            link=link,
        )  # re-runs field validation
        self.kind, self.title, self.body = candidate.kind, candidate.title, candidate.body
        self.starts_at, self.link = candidate.starts_at, candidate.link
        self.status = PostStatus.PENDING
        self.reject_reason = None
        self.published_at = None

    def publish(self, now: datetime) -> None:
        if self.status is not PostStatus.PENDING:
            raise Conflict(f"cannot publish a {self.status.value} post", code="post_state")
        self.status = PostStatus.PUBLISHED
        self.reject_reason = None
        self.published_at = now

    def reject(self, reason: str) -> None:
        if self.status not in (PostStatus.PENDING, PostStatus.PUBLISHED):
            raise Conflict(f"cannot reject a {self.status.value} post", code="post_state")
        reason = reason.strip()
        if not reason:
            raise ValidationFailed("reject reason is required", code="reason_required")
        self.status = PostStatus.REJECTED
        self.reject_reason = reason[:1000]
        self.published_at = None


def validate_description(desc: dict[str, str]) -> dict[str, str]:
    bad = [k for k in desc if k not in LOCALES]
    if bad:
        raise ValidationFailed(f"unsupported locale: {bad[0]}", code="invalid_locale")
    cleaned = {k: v.strip() for k, v in desc.items() if v.strip()}
    if any(len(v) > MAX_BODY for v in cleaned.values()):
        raise ValidationFailed("description too long", code="invalid_description")
    return cleaned


def validate_contacts(contacts: dict[str, str]) -> dict[str, str]:
    bad = [k for k in contacts if k not in CONTACT_KEYS]
    if bad:
        raise ValidationFailed(f"unknown contact: {bad[0]}", code="invalid_contacts")
    cleaned = {k: v.strip() for k, v in contacts.items() if v.strip()}
    if "telegram" in cleaned:
        cleaned["telegram"] = normalize_telegram(cleaned["telegram"]) or ""
    if "phone" in cleaned:
        phones = validate_phones([cleaned["phone"]])
        cleaned["phone"] = phones[0]
    if "email" in cleaned and not EMAIL_RE.fullmatch(cleaned["email"]):
        raise ValidationFailed("invalid email", code="invalid_email")
    return {k: v for k, v in cleaned.items() if v}


def validate_string_list(items: list[str], *, limit: int, code: str) -> list[str]:
    cleaned = list(dict.fromkeys(i.strip() for i in items if i.strip()))
    if any(len(i) > MAX_COURSE_LEN for i in cleaned):
        raise ValidationFailed("item too long", code=code)
    if len(cleaned) > limit:
        raise ValidationFailed("too many items", code=code)
    return cleaned
