"""Which daily question each chat currently holds, so a callback answers it only once.

Callback data is client-controlled (any question id can be forged), so an answer is accepted
only when it matches the question last issued to that chat, and is consumed atomically.
"""

from typing import Protocol
from uuid import UUID

import redis.asyncio as aioredis

from app.settings import get_settings

TTL_SECONDS = 24 * 3600
_CONSUME = (
    "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end return 0"
)


class IssuedStore(Protocol):
    async def issue(self, chat_id: int, question_id: UUID) -> None: ...
    async def consume(self, chat_id: int, question_id: UUID) -> bool: ...


def _key(chat_id: int) -> str:
    return f"bot:daily:{chat_id}"


class RedisIssuedStore:
    def __init__(self, client: "aioredis.Redis") -> None:
        self._r = client

    async def issue(self, chat_id: int, question_id: UUID) -> None:
        await self._r.set(_key(chat_id), str(question_id), ex=TTL_SECONDS)

    async def consume(self, chat_id: int, question_id: UUID) -> bool:
        return bool(await self._r.eval(_CONSUME, 1, _key(chat_id), str(question_id)))  # type: ignore[misc]


_store: IssuedStore | None = None


def get_issued_store() -> IssuedStore:
    global _store
    if _store is None:
        _store = RedisIssuedStore(aioredis.from_url(get_settings().redis_url))
    return _store
