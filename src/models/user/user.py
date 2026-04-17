from datetime import datetime

from pydantic import BaseModel, model_validator


class User(BaseModel):
    """User model."""

    id: str  # uuid v7

    telegram_id: int | None = None

    login: str | None = None
    hashed_password: str | None = None  # bcrypt hash

    # Attempt history lives in the separate 'attempts' collection.
    # Query AttemptRepository.get_by_user(user_id) for full history and analytics.

    created_at: datetime

    @model_validator(mode="after")
    def require_login_or_telegram(self) -> "User":
        if self.login is None and self.telegram_id is None:
            raise ValueError("Either login or telegram_id must be provided")
        return self
