import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.modules.ai.infrastructure.config import AISettings
from app.modules.ai.ports import LLMError, LLMRequest, LLMResponse

_RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class OpenRouterLLM:
    """OpenAI-compatible chat completions on OpenRouter with JSON mode and bounded retries."""

    def __init__(
        self,
        settings: AISettings,
        client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._s = settings
        self._client = client
        self._sleep = sleep

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._s.openrouter_base_url,
                timeout=self._s.ai_http_timeout_seconds,
            )
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not self._s.openrouter_api_key:
            raise LLMError("OPENROUTER_API_KEY is not configured")
        body: dict[str, Any] = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "usage": {"include": True},
        }
        if request.json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {self._s.openrouter_api_key}",
            "HTTP-Referer": self._s.openrouter_referer,
            "X-Title": self._s.openrouter_title,
        }
        attempts = max(1, self._s.ai_max_retries + 1)
        last: LLMError | None = None
        for attempt in range(attempts):
            started = time.monotonic()
            try:
                resp = await self._http().post("/chat/completions", json=body, headers=headers)
            except httpx.TransportError as e:
                last = LLMError(f"transport error: {type(e).__name__}", retryable=True)
            else:
                if resp.status_code in _RETRY_STATUS:
                    last = LLMError(f"upstream {resp.status_code}", retryable=True)
                elif resp.status_code >= 400:
                    raise LLMError(f"upstream {resp.status_code}: {resp.text[:300]}")
                else:
                    return self._parse(resp, request, int((time.monotonic() - started) * 1000))
            if attempt + 1 < attempts:
                await self._sleep(self._s.ai_retry_base_delay_seconds * (3**attempt))
        assert last is not None
        raise last

    @staticmethod
    def _parse(resp: httpx.Response, request: LLMRequest, latency_ms: int) -> LLMResponse:
        try:
            data = resp.json()
            text = data["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise LLMError("malformed upstream response", retryable=False) from e
        usage = data.get("usage") or {}
        cost = usage.get("cost")
        return LLMResponse(
            text=text,
            model=data.get("model") or request.model,
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
            provider_cost_usd=float(cost) if isinstance(cost, int | float) else None,
        )
