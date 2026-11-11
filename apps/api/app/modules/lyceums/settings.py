from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class LyceumsSettings(BaseSettings):
    """Module-local until merged into app.settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    edu_api_base_url: str = "https://my-api.edu.uz/api/v1"
    lyceums_import_concurrency: int = 2  # edu.uz returns 429 on bursts


@lru_cache
def get_lyceums_settings() -> LyceumsSettings:
    return LyceumsSettings()
