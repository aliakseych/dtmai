from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str = "dtmai"

    OPENROUTER_API_KEY: str
    AI_MODEL: str = "google/gemini-2.5-pro-preview"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    TELEGRAM_TOKEN: str
    ADMIN_ID: int

    MINIO_URL: str = "http://127.0.0.1:9000"
    MINIO_USERNAME: str = ""
    MINIO_PASSWORD: str = ""
    MINIO_BUCKET: str = "dtmai"
    MINIO_PUBLIC_URL: str = ""  # Cloudflare tunnel URL, e.g. https://storage.example.com

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
