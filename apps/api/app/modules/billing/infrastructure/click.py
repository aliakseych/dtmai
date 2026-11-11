from urllib.parse import urlencode

from app.modules.billing.domain.click import Invoice
from app.modules.billing.settings import BillingSettings


class ClickShopProvider:
    """Click Shop API adapter (https://docs.click.uz/click-api-request/)."""

    name = "click"

    def __init__(self, settings: BillingSettings) -> None:
        self._s = settings

    def checkout_url(self, invoice: Invoice) -> str:
        query = {
            "service_id": self._s.click_service_id,
            "merchant_id": self._s.click_merchant_id,
            "amount": f"{invoice.amount_uzs}.00",
            "transaction_param": str(invoice.id),
            "return_url": self._s.click_return_url,
        }
        if self._s.click_merchant_user_id:
            query["merchant_user_id"] = self._s.click_merchant_user_id
        return f"{self._s.click_pay_url}?{urlencode(query)}"
