"""`python -m app promote <email> [role ...]`: grant roles to a registered user (first-admin bootstrap)."""

import asyncio
import sys

from sqlalchemy import text

from app.modules.identity.domain.models import normalize_email
from app.shared.db import get_sessionmaker

USAGE = "usage: python -m app promote <email> [role ...]  (default role: admin)"


async def _promote(email: str, roles: list[str]) -> int:
    async with get_sessionmaker()() as session:
        row = await session.execute(
            text(
                "UPDATE identity.users SET roles = ARRAY(SELECT DISTINCT unnest(roles || CAST(:r AS varchar[]))) "
                "WHERE email = :e RETURNING roles"
            ),
            {"e": normalize_email(email), "r": roles},
        )
        got = row.scalar_one_or_none()
        await session.commit()
    if got is None:
        print(f"no user with email {email}; register first", file=sys.stderr)
        return 1
    print(f"{email}: {', '.join(got)}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    return asyncio.run(_promote(argv[0], argv[1:] or ["admin"]))
