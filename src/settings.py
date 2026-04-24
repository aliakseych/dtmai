from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str

    OPENROUTER_API_KEY: str
    AI_MODEL: str = "google/gemini-2.5-pro-preview"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    TELEGRAM_TOKEN: str
    ADMINS_IDS: list[str]

    S3_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str
    S3_PUBLIC_URL: str

    # @field_validator('ADMINS_IDS', mode='before')
    # @classmethod
    # def split_admins_ids(cls, v):
    #     if isinstance(v, str):
    #         return [x.strip() for x in v.split(',')]
    #     return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      extra="ignore")


settings = Settings()
