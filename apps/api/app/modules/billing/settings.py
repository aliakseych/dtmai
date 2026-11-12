from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BillingSettings(BaseSettings):
    """Module-local settings until merged into app.settings (env names are unprefixed)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    payments_enabled: bool = False
    click_service_id: str = ""
    click_merchant_id: str = ""
    click_merchant_user_id: str = ""
    click_secret_key: str = ""
    click_pay_url: str = "https://my.click.uz/services/pay"
    click_return_url: str = "https://app.dtm-ai.uz/premium"
    # CIDRs/IPs allowed to call prepare/complete; empty = no IP restriction.
    click_allowed_ips: list[str] = Field(default_factory=list)


@lru_cache
def get_billing_settings() -> BillingSettings:
    return BillingSettings()
