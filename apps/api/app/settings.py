from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "postgresql+asyncpg://dtmai:dtmai@localhost:5432/dtmai"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    jwt_secret: str = "dev-insecure-change-me"
    access_ttl_seconds: int = 15 * 60
    refresh_ttl_seconds: int = 30 * 24 * 3600

    email_code_ttl_seconds: int = 15 * 60
    email_code_max_attempts: int = 5

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_init_data_max_age_seconds: int = 24 * 3600

    mail_backend: Literal["console", "smtp"] = "console"
    mail_from: str = "DTM AI <no-reply@dtm-ai.uz>"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = False

    openrouter_api_key: str = ""
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "dtmai"

    def assert_production_safe(self) -> None:
        if self.env == "prod" and (len(self.jwt_secret) < 32 or self.jwt_secret.startswith("dev-")):
            raise RuntimeError("JWT_SECRET must be set in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
