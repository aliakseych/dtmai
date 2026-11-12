"""Click Shop API (prepare/complete): signature, error codes and the invoice state machine.

Pure logic; the application layer loads/saves the invoice and publishes events.
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import IntEnum, StrEnum
from uuid import UUID

from app.shared.errors import ValidationFailed


class ClickError(IntEnum):
    SUCCESS = 0
    SIGN_CHECK_FAILED = -1
    INCORRECT_AMOUNT = -2
    ACTION_NOT_FOUND = -3
    ALREADY_PAID = -4
    USER_NOT_FOUND = -5  # merchant_trans_id (invoice) does not exist
    TRANSACTION_NOT_FOUND = -6  # merchant_prepare_id / click_trans_id mismatch
    UPDATE_FAILED = -7
    BAD_REQUEST = -8
    TRANSACTION_CANCELED = -9


ERROR_NOTES = {
    ClickError.SUCCESS: "Success",
    ClickError.SIGN_CHECK_FAILED: "SIGN CHECK FAILED!",
    ClickError.INCORRECT_AMOUNT: "Incorrect parameter amount",
    ClickError.ACTION_NOT_FOUND: "Action not found",
    ClickError.ALREADY_PAID: "Already paid",
    ClickError.USER_NOT_FOUND: "User does not exist",
    ClickError.TRANSACTION_NOT_FOUND: "Transaction does not exist",
    ClickError.UPDATE_FAILED: "Failed to update user",
    ClickError.BAD_REQUEST: "Error in request from click",
    ClickError.TRANSACTION_CANCELED: "Transaction cancelled",
}

ACTION_PREPARE = 0
ACTION_COMPLETE = 1


def _md5(*parts: str) -> str:
    return hashlib.md5("".join(parts).encode(), usedforsecurity=False).hexdigest()  # noqa: S324


def sign_prepare(
    click_trans_id: str,
    service_id: str,
    secret: str,
    merchant_trans_id: str,
    amount: str,
    action: str,
    sign_time: str,
) -> str:
    return _md5(click_trans_id, service_id, secret, merchant_trans_id, amount, action, sign_time)


def sign_complete(
    click_trans_id: str,
    service_id: str,
    secret: str,
    merchant_trans_id: str,
    merchant_prepare_id: str,
    amount: str,
    action: str,
    sign_time: str,
) -> str:
    return _md5(
        click_trans_id,
        service_id,
        secret,
        merchant_trans_id,
        merchant_prepare_id,
        amount,
        action,
        sign_time,
    )


@dataclass(frozen=True, slots=True)
class ClickRequest:
    click_trans_id: str
    service_id: str
    merchant_trans_id: str
    amount: str
    action: str
    sign_time: str
    sign_string: str
    error: int = 0
    click_paydoc_id: str = ""
    merchant_prepare_id: str = ""
    error_note: str = ""

    @classmethod
    def parse(cls, raw: dict[str, str]) -> "ClickRequest":
        required = (
            "click_trans_id",
            "service_id",
            "merchant_trans_id",
            "amount",
            "action",
            "sign_time",
            "sign_string",
        )
        if any(not str(raw.get(k, "")).strip() for k in required):
            raise ValidationFailed("missing click parameters", code="click_bad_request")
        try:
            error = int(raw.get("error") or 0)
        except ValueError as e:
            raise ValidationFailed("bad error field", code="click_bad_request") from e
        return cls(
            click_trans_id=raw["click_trans_id"],
            service_id=raw["service_id"],
            merchant_trans_id=raw["merchant_trans_id"],
            amount=raw["amount"],
            action=raw["action"],
            sign_time=raw["sign_time"],
            sign_string=raw["sign_string"],
            error=error,
            click_paydoc_id=raw.get("click_paydoc_id", ""),
            merchant_prepare_id=raw.get("merchant_prepare_id", ""),
            error_note=raw.get("error_note", ""),
        )

    def expected_sign(self, secret: str) -> str:
        if self.action == str(ACTION_COMPLETE):
            return sign_complete(
                self.click_trans_id,
                self.service_id,
                secret,
                self.merchant_trans_id,
                self.merchant_prepare_id,
                self.amount,
                self.action,
                self.sign_time,
            )
        return sign_prepare(
            self.click_trans_id,
            self.service_id,
            secret,
            self.merchant_trans_id,
            self.amount,
            self.action,
            self.sign_time,
        )

    def sign_is_valid(self, secret: str) -> bool:
        return hmac.compare_digest(self.expected_sign(secret), self.sign_string.lower())


class InvoiceStatus(StrEnum):
    PENDING = "pending"
    PREPARED = "prepared"
    PAID = "paid"
    CANCELED = "canceled"


@dataclass(slots=True)
class Invoice:
    id: UUID
    seq: int  # merchant_prepare_id
    user_id: UUID
    plan_code: str
    period_months: int
    amount_uzs: int
    status: InvoiceStatus = InvoiceStatus.PENDING
    click_trans_id: str | None = None
    click_paydoc_id: str | None = None
    paid_at: datetime | None = None
    canceled_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ClickOutcome:
    error: ClickError
    paid: bool = False  # True only the first time the invoice turns paid

    @property
    def note(self) -> str:
        return ERROR_NOTES[self.error]


def _amount_matches(raw: str, expected: int) -> bool:
    try:
        return Decimal(raw) == Decimal(expected)
    except InvalidOperation:
        return False


def handle_click(
    req: ClickRequest, invoice: Invoice | None, *, secret: str, service_id: str, now: datetime
) -> ClickOutcome:
    """Apply a Click request to `invoice` (mutated in place) and return the response code."""
    if req.service_id != service_id or not req.sign_is_valid(secret):
        return ClickOutcome(ClickError.SIGN_CHECK_FAILED)
    if req.action not in (str(ACTION_PREPARE), str(ACTION_COMPLETE)):
        return ClickOutcome(ClickError.ACTION_NOT_FOUND)
    if invoice is None:
        return ClickOutcome(ClickError.USER_NOT_FOUND)
    if not _amount_matches(req.amount, invoice.amount_uzs):
        return ClickOutcome(ClickError.INCORRECT_AMOUNT)
    if req.action == str(ACTION_PREPARE):
        return _prepare(req, invoice)
    return _complete(req, invoice, now)


def _prepare(req: ClickRequest, inv: Invoice) -> ClickOutcome:
    if inv.status is InvoiceStatus.PAID:
        return ClickOutcome(ClickError.ALREADY_PAID)
    if inv.status is InvoiceStatus.CANCELED:
        return ClickOutcome(ClickError.TRANSACTION_CANCELED)
    if inv.status is InvoiceStatus.PREPARED:
        # Idempotent on click_trans_id; a different Click transaction cannot take over.
        if inv.click_trans_id == req.click_trans_id:
            return ClickOutcome(ClickError.SUCCESS)
        return ClickOutcome(ClickError.UPDATE_FAILED)
    if req.error < 0:
        return ClickOutcome(ClickError.TRANSACTION_CANCELED)
    inv.status = InvoiceStatus.PREPARED
    inv.click_trans_id = req.click_trans_id
    inv.click_paydoc_id = req.click_paydoc_id or None
    return ClickOutcome(ClickError.SUCCESS)


def _complete(req: ClickRequest, inv: Invoice, now: datetime) -> ClickOutcome:
    if req.merchant_prepare_id != str(inv.seq) or inv.status is InvoiceStatus.PENDING:
        return ClickOutcome(ClickError.TRANSACTION_NOT_FOUND)
    if inv.click_trans_id != req.click_trans_id:
        return ClickOutcome(ClickError.TRANSACTION_NOT_FOUND)
    if inv.status is InvoiceStatus.PAID:
        return ClickOutcome(ClickError.ALREADY_PAID)
    if inv.status is InvoiceStatus.CANCELED:
        return ClickOutcome(ClickError.TRANSACTION_CANCELED)
    if req.error < 0:
        inv.status = InvoiceStatus.CANCELED
        inv.canceled_at = now
        return ClickOutcome(ClickError.TRANSACTION_CANCELED)
    inv.status = InvoiceStatus.PAID
    inv.paid_at = now
    return ClickOutcome(ClickError.SUCCESS, paid=True)
