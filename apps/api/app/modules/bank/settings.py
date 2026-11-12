from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BankSettings(BaseSettings):
    """Module-local until merged into app.settings (env vars CONTENT_MIN_POOL, ...)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    content_min_pool: int = 30
    question_report_hide_threshold: int = 3


@lru_cache
def get_bank_settings() -> BankSettings:
    return BankSettings()
