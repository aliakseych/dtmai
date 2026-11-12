from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class LabelingSettings(BaseSettings):
    """Module-local until merged into app.settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    labeling_audit_ratio: float = 0.1
    labeling_min_models: int = 2
    labeling_min_confidence: float = 0.7
    labeling_bulk_min_agreement: float = 0.95
    labeling_autogen_per_question: int = 2
    labeling_autogen_max_per_batch: int = 60
    labeling_upload_dir: str = "./.uploads"


@lru_cache
def get_labeling_settings() -> LabelingSettings:
    return LabelingSettings()
