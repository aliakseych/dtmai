from uuid import UUID

from app.modules.ai.application.errors import AIBudgetExhausted, AIUnavailable, AIUpstreamFailed
from app.modules.ai.domain.budget import (
    BudgetExceeded,
    check_call_allowed,
    estimate_cost_micro,
    usd_to_micro,
)
from app.modules.ai.domain.jsonparse import parse_json_object
from app.modules.ai.domain.routing import ModelRoute, Task
from app.modules.ai.ports import (
    AIConfigRepository,
    LedgerEntry,
    LedgerRepository,
    LLMError,
    LLMMessage,
    LLMPort,
    LLMRequest,
    LLMResponse,
)


class AIGateway:
    """Single door for every LLM call: route lookup, kill-switch, user budget, ledger."""

    def __init__(self, llm: LLMPort, config: AIConfigRepository, ledger: LedgerRepository) -> None:
        self._llm = llm
        self._config = config
        self._ledger = ledger

    async def routes(self, task: Task) -> list[ModelRoute]:
        routes = await self._config.routes_for(task)
        if not routes:
            raise AIUnavailable(f"no enabled model route for task '{task.value}'")
        return routes

    async def complete(
        self,
        route: ModelRoute,
        messages: list[LLMMessage],
        *,
        purpose: str,
        user_id: UUID | None = None,
        ref: str | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        limits = await self._config.limits()
        try:
            check_call_allowed(
                limits,
                spent_today_micro=await self._ledger.spent_today_micro(),
                user_tokens_today=(
                    await self._ledger.user_tokens_today(user_id) if user_id is not None else None
                ),
            )
        except BudgetExceeded as e:
            raise AIBudgetExhausted(e.detail, code=e.code) from e

        request = LLMRequest(
            model=route.model,
            messages=messages,
            json_mode=json_mode,
            temperature=route.temperature,
            max_tokens=route.max_tokens,
        )
        try:
            response = await self._llm.complete(request)
        except LLMError as e:
            await self._ledger.add(
                LedgerEntry(
                    user_id,
                    purpose,
                    route.task.value,
                    route.model,
                    0,
                    0,
                    0,
                    False,
                    0,
                    ref,
                    e.detail[:500],
                )
            )
            raise AIUpstreamFailed(e.detail) from e
        cost = (
            usd_to_micro(response.provider_cost_usd)
            if response.provider_cost_usd is not None
            else estimate_cost_micro(
                response.tokens_in,
                response.tokens_out,
                route.price_in_micro_per_mtok,
                route.price_out_micro_per_mtok,
            )
        )
        await self._ledger.add(
            LedgerEntry(
                user_id,
                purpose,
                route.task.value,
                route.model,
                response.tokens_in,
                response.tokens_out,
                cost,
                True,
                response.latency_ms,
                ref,
            )
        )
        return response

    async def complete_json(
        self,
        route: ModelRoute,
        messages: list[LLMMessage],
        *,
        purpose: str,
        user_id: UUID | None = None,
        ref: str | None = None,
    ) -> tuple[dict[str, object], LLMResponse]:
        """JSON-mode call; one repair retry when the reply is not a JSON object."""
        last_err: ValueError | None = None
        for _ in range(2):
            response = await self.complete(
                route, messages, purpose=purpose, user_id=user_id, ref=ref, json_mode=True
            )
            try:
                return parse_json_object(response.text), response
            except ValueError as e:
                last_err = e
        raise AIUpstreamFailed(f"model returned invalid JSON: {last_err}")
