from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """Module-local settings until merged into app.settings (same env names)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_referer: str = "https://dtm-ai.uz"
    openrouter_title: str = "DTM AI"
    ai_http_timeout_seconds: float = 90.0
    ai_max_retries: int = 3
    ai_explain_timeout_seconds: float = 40.0  # hard cap for one explain request incl. retries
    ai_retry_base_delay_seconds: float = 2.0
    ai_temur_daily_quota: int = (
        20  # free Ask Temur messages per user per Tashkent day; -1 unlimited
    )
    ai_explanations_per_day_default: int = 3


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()
