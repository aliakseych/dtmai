import asyncio
import base64
import json
import logging
from pathlib import Path

from openai import AsyncOpenAI, RateLimitError

from src.interfaces.ai.schemas import AIQuestionResponse
from src.interfaces.ai.subjects.base import SubjectConfig
from src.settings import settings

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # seconds between retries on 429


class AIService:
    """Calls Gemini via OpenRouter to extract a question from an image."""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )

    async def extract_question(
        self,
        image_path: Path,
        config: SubjectConfig,
        categories: list[str],
        semaphore: asyncio.Semaphore | None = None,
    ) -> AIQuestionResponse | None:
        """
        Returns a validated AIQuestionResponse or None if extraction fails.
        Pass a semaphore to cap concurrent in-flight requests.
        """
        if semaphore:
            async with semaphore:
                return await self._call(image_path, config, categories)
        return await self._call(image_path, config, categories)

    async def _call(
        self,
        image_path: Path,
        config: SubjectConfig,
        categories: list[str],
    ) -> AIQuestionResponse | None:
        categories_text = json.dumps(categories, ensure_ascii=False)
        prompt = config.prompt_template.format(categories=categories_text)

        image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
        suffix = image_path.suffix.lower().lstrip(".")
        mime = f"image/{suffix}" if suffix in {"png", "jpg", "jpeg", "webp", "gif"} else "image/jpeg"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
                ],
            }
        ]

        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                logger.info("→ Requesting: %s", image_path.name)
                response = await self._client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                logger.info("← Received:   %s", image_path.name)
                break
            except RateLimitError:
                if delay is None:
                    logger.error("Rate limit: giving up on %s after %d attempts", image_path.name, attempt)
                    return None
                logger.warning("Rate limit hit for %s — retrying in %ds (attempt %d)", image_path.name, delay, attempt)
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error("API call failed for %s: %s", image_path.name, e)
                return None

        raw = response.choices[0].message.content
        try:
            return AIQuestionResponse.model_validate(json.loads(raw))
        except Exception as e:
            logger.error("Parse error for %s: %s\nRaw: %s", image_path.name, e, raw)
            return None
