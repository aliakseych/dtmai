from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class NotifySettings(BaseSettings):
    """Module-local until merged into app.settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_api_base: str = "https://api.telegram.org"
    telegram_bot_username: str = "dtm_ai_bot"
    telegram_mini_app_url: str = "https://dtm-ai.uz/tg"
    telegram_webhook_url: str = "https://api.dtm-ai.uz/tg/webhook"
    fcm_project_id: str = ""
    # Path to a Google service-account JSON file, or the JSON itself. Empty disables push.
    fcm_service_account: str = ""
    link_code_ttl_seconds: int = 15 * 60


@lru_cache
def get_notify_settings() -> NotifySettings:
    return NotifySettings()
