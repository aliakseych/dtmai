from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.modules.ai.domain.budget import Limits
from app.modules.ai.domain.routing import ModelRoute, Task


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str  # system | user | assistant
    content: str | list[dict[str, Any]]  # str or OpenAI-style multimodal parts


@dataclass(frozen=True, slots=True)
class LLMRequest:
    model: str
    messages: list[LLMMessage]
    json_mode: bool = False
    temperature: float = 0.2
    max_tokens: int = 2048


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    provider_cost_usd: float | None = None


class LLMError(Exception):
    def __init__(self, detail: str, *, retryable: bool = False) -> None:
        super().__init__(detail)
        self.detail = detail
        self.retryable = retryable


class LLMPort(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...


class ActiveMockChecker(Protocol):
    """Registered by the assessment module; the tutor refuses while a mock attempt is active."""

    async def has_active_mock(self, user_id: UUID) -> bool: ...


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    user_id: UUID | None
    purpose: str
    task: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_micro: int
    ok: bool
    latency_ms: int
    ref: str | None = None
    error: str | None = None
    created_at: datetime | None = field(default=None)


class AIConfigRepository(Protocol):
    async def routes_for(self, task: Task) -> list[ModelRoute]: ...
    async def all_routes(self) -> list[ModelRoute]: ...
    async def upsert_route(self, route: ModelRoute, actor: UUID) -> None: ...
    async def delete_route(self, task: Task, slot: int) -> bool: ...
    async def limits(self) -> Limits: ...
    async def set_limits(self, limits: Limits, actor: UUID) -> None: ...


class TutorSlotLock(Protocol):
    """Serializes a user's tutor chats so the quota check and the counted ledger write are atomic."""

    def hold(self, user_id: UUID) -> AbstractAsyncContextManager[None]: ...


class LedgerRepository(Protocol):
    async def add(self, entry: LedgerEntry) -> None: ...
    async def spent_today_micro(self) -> int: ...
    async def user_tokens_today(self, user_id: UUID) -> int: ...
    async def user_calls_today(self, user_id: UUID, purpose: str) -> int: ...
    async def spend_report(self, days: int) -> "SpendReport": ...


@dataclass(frozen=True, slots=True)
class SpendRow:
    key: str
    calls: int
    tokens_in: int
    tokens_out: int
    cost_micro: int


@dataclass(frozen=True, slots=True)
class SpendReport:
    by_day: list[SpendRow]
    by_task: list[SpendRow]
    by_model: list[SpendRow]
    by_purpose: list[SpendRow]
