import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from app.modules.identity.domain import telegram
from app.modules.identity.domain.models import (
    EmailCode,
    RefreshToken,
    Role,
    User,
    adopt_guest_profile,
    dream_field_mismatch,
    ensure_admin_change_allowed,
    guest_cutoff,
    locale_from_telegram,
    normalize_email,
    parse_role_set,
    parse_roles,
    validate_city,
    validate_dream_lyceum_ids,
    validate_field_code,
    validate_locale,
    validate_password,
    validate_subject_ids,
)
from app.modules.identity.ports import (
    CityCatalog,
    Clock,
    EmailCodeRepository,
    FieldCatalog,
    Mailer,
    PasswordHasher,
    RefreshTokenRepository,
    UserRepository,
)
from app.shared.errors import Conflict, Forbidden, NotFound, Unauthorized, ValidationFailed
from app.shared.ids import new_id
from app.shared.security import encode_access_token

UNSET = object()
LABELER_DOMAIN = "labelers.dtm-ai.uz"


@dataclass(frozen=True, slots=True)
class IdentityConfig:
    access_ttl: int
    refresh_ttl: int
    code_ttl: int
    code_max_attempts: int
    bot_token: str
    init_data_max_age: int
    jwt_secret: str


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class IdentityService:
    def __init__(
        self,
        users: UserRepository,
        codes: EmailCodeRepository,
        refresh: RefreshTokenRepository,
        hasher: PasswordHasher,
        mailer: Mailer,
        clock: Clock,
        config: IdentityConfig,
        cities: CityCatalog,
        fields: FieldCatalog,
    ) -> None:
        self._users, self._codes, self._refresh = users, codes, refresh
        self._hasher, self._mailer, self._clock, self._cfg = hasher, mailer, clock, config
        self._cities, self._fields = cities, fields

    async def register_email(self, email: str, password: str, name: str, locale: str) -> None:
        email = normalize_email(email)
        validate_password(password)
        validate_locale(locale)
        existing = await self._users.by_email(email)
        if existing and existing.email_verified:
            raise Conflict("email already registered", code="email_taken")
        if existing:
            existing.password_hash = self._hasher.hash(password)
            existing.rename(name)
            existing.locale = locale
            await self._users.save(existing)
            user = existing
        else:
            user = User(
                id=new_id(),
                name=name.strip() or email,
                locale=locale,
                email=email,
                password_hash=self._hasher.hash(password),
            )
            user.rename(user.name)
            await self._users.add(user)
        await self._send_code(user)

    async def resend_code(self, email: str) -> None:
        user = await self._users.by_email(normalize_email(email))
        if user and not user.email_verified:
            await self._send_code(user)

    async def _consume_code(self, user: User | None, code: str) -> User:
        """Validate + consume the latest email code; any failure is an indistinguishable `invalid_code`."""
        if user is None:
            raise ValidationFailed("invalid code", code="invalid_code")
        stored = await self._codes.latest_for(user.id)
        now = self._clock.now()
        if (
            stored is None
            or stored.consumed
            or stored.expires_at < now
            or stored.attempts >= self._cfg.code_max_attempts
        ):
            raise ValidationFailed("code expired or exhausted", code="invalid_code")
        if not hmac.compare_digest(stored.code_hash, _sha(f"{user.id}:{code.strip()}")):
            await self._codes.record_attempt(stored.id)
            raise ValidationFailed("invalid code", code="invalid_code")
        await self._codes.consume(stored.id)
        return user

    async def verify_email(self, email: str, code: str) -> TokenPair:
        user = await self._consume_code(await self._users.by_email(normalize_email(email)), code)
        user.email_verified = True
        await self._users.save(user)
        return await self._issue(user)

    async def forgot_password(self, email: str) -> None:
        """Email a reset code. Silent for unknown emails (no account enumeration)."""
        user = await self._users.by_email(normalize_email(email))
        if user:
            await self._send_code(user, purpose="password reset")

    async def reset_password(self, email: str, code: str, password: str) -> TokenPair:
        validate_password(password)
        user = await self._consume_code(await self._users.by_email(normalize_email(email)), code)
        user.password_hash = self._hasher.hash(password)
        user.email_verified = True  # the code proves mailbox ownership
        await self._users.save(user)
        return await self._issue(user)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.by_email(normalize_email(email))
        if (
            user is None
            or not user.password_hash
            or not self._hasher.verify(password, user.password_hash)
        ):
            raise Unauthorized("wrong email or password", code="invalid_credentials")
        if not user.email_verified:
            raise Forbidden("email not verified", code="email_not_verified")
        return await self._issue(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        stored = await self._refresh.by_hash(_sha(refresh_token))
        if stored is None or stored.revoked or stored.expires_at < self._clock.now():
            raise Unauthorized("invalid refresh token", code="invalid_refresh")
        await self._refresh.revoke(stored.id)
        user = await self._users.get(stored.user_id)
        if user is None:
            raise Unauthorized("invalid refresh token", code="invalid_refresh")
        return await self._issue(user)

    async def logout(self, refresh_token: str) -> None:
        stored = await self._refresh.by_hash(_sha(refresh_token))
        if stored and not stored.revoked:
            await self._refresh.revoke(stored.id)

    async def login_telegram_webapp(self, init_data: str) -> TokenPair:
        profile = telegram.verify_init_data(
            init_data, self._cfg.bot_token, max_age=self._cfg.init_data_max_age
        )
        return await self._login_profile(profile)

    async def login_telegram_widget(self, data: dict[str, str]) -> TokenPair:
        profile = telegram.verify_login_widget(
            data, self._cfg.bot_token, max_age=self._cfg.init_data_max_age
        )
        return await self._login_profile(profile)

    async def create_guest(self) -> TokenPair:
        user = User(id=new_id(), name="Guest", roles={Role.GUEST})
        await self._users.add(user)
        return await self._issue(user)

    async def list_users(
        self,
        q: str | None,
        role: str | None,
        status: str | None,
        sort: str,
        descending: bool,
        page: int,
        size: int,
    ) -> tuple[int, list[User]]:
        disabled = None if status is None else status == "disabled"
        return await self._users.search(
            q, role, disabled, sort, descending, size, (page - 1) * size
        )

    async def get_many(self, ids: list[UUID]) -> dict[UUID, User]:
        return {u.id: u for u in await self._users.get_many(ids)}

    async def update_user(
        self,
        actor_id: UUID,
        user_id: UUID,
        *,
        roles: list[str] | None = None,
        status: str | None = None,
        display_name: str | None = None,
    ) -> User:
        user = await self.get_me(user_id)
        new_roles = (
            parse_roles(roles, actor_id=actor_id, target_id=user_id)
            if roles is not None
            else user.roles
        )
        disabled = user.disabled if status is None else status == "disabled"
        ensure_admin_change_allowed(
            actor_id=actor_id,
            target=user,
            new_roles=new_roles,
            disabled=disabled,
            active_admins=await self._users.count_active_admins(),
        )
        user.roles, user.disabled = new_roles, disabled
        if display_name is not None:
            user.rename(display_name)
        await self._users.save(user)
        return user

    async def create_staff(
        self, email: str, password: str, name: str, raw_roles: list[str]
    ) -> User:
        email = normalize_email(email)
        validate_password(password)
        roles = parse_role_set(raw_roles)
        if Role.GUEST in roles:
            raise ValidationFailed("staff cannot be guests", code="invalid_role")
        if await self._users.by_email(email):
            raise Conflict("email already registered", code="email_taken")
        user = User(
            id=new_id(),
            name=name.strip() or email,
            email=email,
            email_verified=True,
            password_hash=self._hasher.hash(password),
            roles=roles,
        )
        user.rename(user.name)
        await self._users.add(user)
        return user

    async def create_labeler(self, name: str | None) -> tuple[User, str, str]:
        """A system labeler account; returns (user, login, password) — the password is shown once."""
        login = f"labeler-{secrets.token_hex(4)}@{LABELER_DOMAIN}"
        password = secrets.token_urlsafe(12)
        user = User(
            id=new_id(),
            name=(name or "").strip() or login,
            email=login,
            email_verified=True,
            password_hash=self._hasher.hash(password),
            roles={Role.LABELER},
            is_system=True,
        )
        await self._users.add(user)
        return user, login, password

    async def reset_user_password(self, user_id: UUID, password: str) -> None:
        validate_password(password)
        user = await self.get_me(user_id)
        user.password_hash = self._hasher.hash(password)
        await self._users.save(user)
        await self._refresh.revoke_all(user_id)

    async def retire_guest(self, guest_id: UUID, into_id: UUID | None = None) -> None:
        """After a guest's progress was merged: carry its profile into `into_id`, disable it, kill its sessions."""
        user = await self.get_me(guest_id)
        if Role.GUEST not in user.roles:
            raise Forbidden("user is not a guest", code="not_a_guest")
        if into_id is not None:
            target = await self.get_me(into_id)
            adopt_guest_profile(target, user)
            await self._users.save(target)
        user.disabled = True
        await self._users.save(user)
        await self._refresh.revoke_all(guest_id)

    async def contacts(
        self, after: UUID | None, limit: int, locale: str | None = None, with_email: bool = False
    ) -> list[User]:
        return await self._users.contacts(after, limit, locale, with_email)

    async def get_me(self, user_id: UUID) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise NotFound("user not found", code="user_not_found")
        return user

    async def update_me(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        locale: str | None = None,
        dream_lyceum_ids: list[UUID] | object = UNSET,
        education_language_id: UUID | None | object = UNSET,
        city: str | None | object = UNSET,
        field_code: str | None | object = UNSET,
        subject_ids: list[UUID] | object = UNSET,
    ) -> User:
        user = await self.get_me(user_id)
        if name is not None:
            user.rename(name)
        if locale is not None:
            user.locale = validate_locale(locale)
        if dream_lyceum_ids is not UNSET:
            user.dream_lyceum_ids = validate_dream_lyceum_ids(dream_lyceum_ids)  # type: ignore[arg-type]
        if education_language_id is not UNSET:
            user.education_language_id = education_language_id  # type: ignore[assignment]
        if city is not UNSET:
            code = validate_city(city)  # type: ignore[arg-type]
            if code is not None and not await self._cities.exists(code):
                raise ValidationFailed("unknown city", code="unknown_city")
            user.city = code
        if subject_ids is not UNSET:
            user.subject_ids = validate_subject_ids(subject_ids)  # type: ignore[arg-type]
        if field_code is not UNSET:
            user.field_code = validate_field_code(field_code)  # type: ignore[arg-type]
        if user.field_code is not None and (field_code is not UNSET or subject_ids is not UNSET):
            # The field decides the subjects; explicit ones stay only when it has no mapping.
            mapped = await self._fields.subjects_for(user.field_code)
            if mapped:
                user.subject_ids = validate_subject_ids(mapped)
        await self._users.save(user)
        return user

    async def dream_field_mismatch(self, user: User) -> list[UUID]:
        """Dream lyceums that do not offer the user's field (informational, never rejected)."""
        if user.field_code is None or not user.dream_lyceum_ids:
            return []
        offered = await self._fields.offered_fields(user.dream_lyceum_ids)
        return dream_field_mismatch(user.field_code, user.dream_lyceum_ids, offered)

    async def grant_role(self, user_id: UUID, role: Role) -> User:
        """Add a role (idempotent). Guests cannot hold other roles."""
        user = await self.get_me(user_id)
        if Role.GUEST in user.roles:
            raise ValidationFailed("guest cannot be combined with other roles", code="invalid_role")
        if role not in user.roles:
            user.roles = user.roles | {role}
            await self._users.save(user)
        return user

    async def count_dreamers(self, lyceum_id: UUID) -> int:
        return await self._users.count_by_dream_lyceum(lyceum_id)

    async def cleanup_guests(self) -> int:
        """Delete guest accounts inactive for more than the retention window."""
        return await self._users.delete_guests_unseen_since(guest_cutoff(self._clock.now()))

    async def _login_profile(self, profile: telegram.TelegramProfile) -> TokenPair:
        user = await self._users.by_telegram_id(profile.id)
        if user is None:
            user = User(
                id=new_id(),
                name=profile.display_name,
                locale=locale_from_telegram(profile.language_code),
                telegram_id=profile.id,
                telegram_username=profile.username,
            )
            await self._users.add(user)
        elif profile.username != user.telegram_username:
            user.telegram_username = profile.username
            await self._users.save(user)
        return await self._issue(user)

    async def _send_code(self, user: User, *, purpose: str = "verification") -> None:
        if not user.email:
            raise ValidationFailed("user has no email", code="no_email")
        code = f"{secrets.randbelow(1_000_000):06d}"
        await self._codes.add(
            EmailCode(
                id=new_id(),
                user_id=user.id,
                code_hash=_sha(f"{user.id}:{code}"),
                expires_at=self._clock.now() + timedelta(seconds=self._cfg.code_ttl),
            )
        )
        await self._mailer.send(
            user.email, "DTM AI: " + code, f"Your DTM AI {purpose} code: {code}"
        )

    async def _issue(self, user: User) -> TokenPair:
        if user.disabled:
            raise Forbidden("account disabled", code="account_disabled")
        await self._users.touch(user.id, self._clock.now())
        raw = secrets.token_urlsafe(48)
        await self._refresh.add(
            RefreshToken(
                id=new_id(),
                user_id=user.id,
                token_hash=_sha(raw),
                expires_at=self._clock.now() + timedelta(seconds=self._cfg.refresh_ttl),
            )
        )
        access = encode_access_token(
            user.id,
            {r.value for r in user.roles},
            secret=self._cfg.jwt_secret,
            ttl_seconds=self._cfg.access_ttl,
            now=self._clock.now(),
        )
        return TokenPair(access, raw, self._cfg.access_ttl)
