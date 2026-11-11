from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.models import EmailCode, RefreshToken, Role, User
from app.modules.identity.infrastructure.orm import EmailCodeRow, RefreshTokenRow, UserRow
from app.shared.errors import Conflict

ACTIVE, DISABLED = "active", "disabled"


def _to_domain(r: UserRow) -> User:
    return User(
        id=r.id, name=r.name, locale=r.locale, email=r.email, email_verified=r.email_verified,
        password_hash=r.password_hash, telegram_id=r.telegram_id,
        roles={Role(x) for x in r.roles}, dream_lyceum_ids=list(r.dream_lyceum_ids or []),
        education_language_id=r.education_language_id, city=r.city, field_code=r.field_code,
        subject_ids=list(r.subject_ids or []), created_at=r.created_at,
        last_seen_at=r.last_seen_at, telegram_username=r.telegram_username,
        disabled=r.status == DISABLED, is_system=r.is_system,
    )


def _fill(r: UserRow, u: User) -> None:
    r.email, r.email_verified, r.password_hash = u.email, u.email_verified, u.password_hash
    r.telegram_id, r.name, r.locale = u.telegram_id, u.name, u.locale
    r.roles = sorted(x.value for x in u.roles)
    r.dream_lyceum_ids, r.education_language_id = list(u.dream_lyceum_ids), u.education_language_id
    r.city, r.subject_ids = u.city, list(u.subject_ids)
    r.field_code = u.field_code
    r.telegram_username, r.is_system = u.telegram_username, u.is_system
    r.status = DISABLED if u.disabled else ACTIVE


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _one(self, *where: object) -> User | None:
        row = (await self._s.execute(select(UserRow).where(*where))).scalar_one_or_none()  # type: ignore[arg-type]
        return _to_domain(row) if row else None

    async def get(self, user_id: UUID) -> User | None:
        return await self._one(UserRow.id == user_id)

    async def by_email(self, email: str) -> User | None:
        return await self._one(UserRow.email == email)

    async def by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._one(UserRow.telegram_id == telegram_id)

    async def add(self, user: User) -> None:
        row = UserRow(id=user.id)
        _fill(row, user)
        self._s.add(row)
        try:
            await self._s.flush()
        except IntegrityError as e:
            raise Conflict("user already exists", code="user_exists") from e

    async def save(self, user: User) -> None:
        row = await self._s.get(UserRow, user.id)
        if row is None:
            raise Conflict("user vanished", code="user_missing")
        _fill(row, user)
        await self._s.flush()

    async def search(
        self, q: str | None, role: str | None, disabled: bool | None, sort: str, descending: bool,
        limit: int, offset: int,
    ) -> tuple[int, list[User]]:
        conds = []
        if q and q.strip():
            term = q.strip()
            like = "%" + term.replace("%", r"\%").replace("_", r"\_") + "%"
            parts = [
                UserRow.email.ilike(like, escape="\\"), UserRow.name.ilike(like, escape="\\"),
                UserRow.telegram_username.ilike(like, escape="\\"),
            ]
            if term.isdigit():
                parts.append(UserRow.telegram_id == int(term))
            conds.append(or_(*parts))
        if role:
            conds.append(UserRow.roles.contains([role]))
        if disabled is not None:
            conds.append(UserRow.status == (DISABLED if disabled else ACTIVE))
        column = {"created_at": UserRow.created_at, "last_seen_at": UserRow.last_seen_at, "email": UserRow.email}[sort]
        total = (await self._s.execute(select(func.count()).select_from(UserRow).where(*conds))).scalar_one()
        rows = (
            await self._s.execute(
                select(UserRow).where(*conds)
                .order_by(column.desc() if descending else column.asc(), UserRow.id)
                .limit(limit).offset(offset)
            )
        ).scalars().all()
        return total, [_to_domain(r) for r in rows]

    async def get_many(self, ids: list[UUID]) -> list[User]:
        if not ids:
            return []
        rows = (await self._s.execute(select(UserRow).where(UserRow.id.in_(ids)))).scalars().all()
        return [_to_domain(r) for r in rows]

    async def count_active_admins(self) -> int:
        stmt = select(func.count()).select_from(UserRow).where(
            UserRow.roles.contains(["admin"]), UserRow.status == ACTIVE
        )
        return int((await self._s.execute(stmt)).scalar_one())

    async def contacts(
        self, after: UUID | None, limit: int, locale: str | None, with_email: bool
    ) -> list[User]:
        stmt = select(UserRow).order_by(UserRow.id).limit(limit)
        if after is not None:
            stmt = stmt.where(UserRow.id > after)
        if locale:
            stmt = stmt.where(UserRow.locale == locale)
        if with_email:
            stmt = stmt.where(UserRow.email.is_not(None), UserRow.email_verified.is_(True))
        return [_to_domain(r) for r in (await self._s.execute(stmt)).scalars()]


    async def touch(self, user_id: UUID, now: datetime) -> None:
        await self._s.execute(
            update(UserRow).where(UserRow.id == user_id).values(last_seen_at=now)
        )

    async def delete_guests_unseen_since(self, cutoff: datetime) -> int:
        """Delete pure-guest users not seen since `cutoff`; tokens/codes cascade."""
        result = await self._s.execute(
            delete(UserRow).where(
                UserRow.roles == [Role.GUEST.value], UserRow.last_seen_at < cutoff
            )
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]

    async def count_by_dream_lyceum(self, lyceum_id: UUID) -> int:
        return int(
            (
                await self._s.execute(
                    select(func.count()).select_from(UserRow).where(
                        UserRow.dream_lyceum_ids.contains([lyceum_id])
                    )
                )
            ).scalar_one()
        )


class SqlEmailCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, code: EmailCode) -> None:
        self._s.add(
            EmailCodeRow(
                id=code.id, user_id=code.user_id, code_hash=code.code_hash,
                expires_at=code.expires_at, attempts=code.attempts, consumed=code.consumed,
            )
        )
        await self._s.flush()

    async def latest_for(self, user_id: UUID) -> EmailCode | None:
        r = (
            await self._s.execute(
                select(EmailCodeRow)
                .where(EmailCodeRow.user_id == user_id)
                .order_by(EmailCodeRow.created_at.desc(), EmailCodeRow.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if r is None:
            return None
        return EmailCode(r.id, r.user_id, r.code_hash, r.expires_at, r.attempts, r.consumed)

    async def record_attempt(self, code_id: UUID) -> None:
        await self._s.execute(
            update(EmailCodeRow)
            .where(EmailCodeRow.id == code_id)
            .values(attempts=EmailCodeRow.attempts + 1)
        )
        # Commit now: the caller raises right after, which would roll the attempt back.
        await self._s.commit()

    async def consume(self, code_id: UUID) -> None:
        await self._s.execute(
            update(EmailCodeRow).where(EmailCodeRow.id == code_id).values(consumed=True)
        )


class SqlRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, token: RefreshToken) -> None:
        self._s.add(
            RefreshTokenRow(
                id=token.id, user_id=token.user_id, token_hash=token.token_hash,
                expires_at=token.expires_at, revoked=token.revoked,
            )
        )
        await self._s.flush()

    async def by_hash(self, token_hash: str) -> RefreshToken | None:
        r = (
            await self._s.execute(
                select(RefreshTokenRow).where(RefreshTokenRow.token_hash == token_hash)
            )
        ).scalar_one_or_none()
        if r is None:
            return None
        return RefreshToken(r.id, r.user_id, r.token_hash, r.expires_at, r.revoked)

    async def revoke(self, token_id: UUID) -> None:
        await self._s.execute(
            update(RefreshTokenRow).where(RefreshTokenRow.id == token_id).values(revoked=True)
        )

    async def revoke_all(self, user_id: UUID) -> None:
        await self._s.execute(
            update(RefreshTokenRow)
            .where(RefreshTokenRow.user_id == user_id, RefreshTokenRow.revoked.is_(False))
            .values(revoked=True)
        )
