from datetime import UTC, datetime
from uuid import uuid4

from app.modules.billing.domain.click import (
    ClickError,
    ClickRequest,
    Invoice,
    InvoiceStatus,
    handle_click,
    sign_complete,
    sign_prepare,
)

SECRET = "s3cret"
SERVICE = "999"
NOW = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


def invoice(**kw: object) -> Invoice:
    base = dict(id=uuid4(), seq=42, user_id=uuid4(), plan_code="premium_1m",
                period_months=1, amount_uzs=49000)
    base.update(kw)
    return Invoice(**base)  # type: ignore[arg-type]


def prepare_req(inv: Invoice, *, trans: str = "100", amount: str = "49000.00",
                secret: str = SECRET, error: int = 0, action: str = "0") -> ClickRequest:
    sign = sign_prepare(trans, SERVICE, secret, str(inv.id), amount, action, "2026-11-11 17:00:00")
    return ClickRequest.parse({
        "click_trans_id": trans, "service_id": SERVICE, "merchant_trans_id": str(inv.id),
        "amount": amount, "action": action, "sign_time": "2026-11-11 17:00:00",
        "sign_string": sign, "error": str(error), "click_paydoc_id": "7",
    })


def complete_req(inv: Invoice, *, trans: str = "100", prepare_id: str | None = None,
                 amount: str = "49000.00", error: int = 0) -> ClickRequest:
    pid = prepare_id if prepare_id is not None else str(inv.seq)
    sign = sign_complete(trans, SERVICE, SECRET, str(inv.id), pid, amount, "1", "2026-11-11 17:00:05")
    return ClickRequest.parse({
        "click_trans_id": trans, "service_id": SERVICE, "merchant_trans_id": str(inv.id),
        "merchant_prepare_id": pid, "amount": amount, "action": "1",
        "sign_time": "2026-11-11 17:00:05", "sign_string": sign, "error": str(error),
    })


def run(req: ClickRequest, inv: Invoice | None):
    return handle_click(req, inv, secret=SECRET, service_id=SERVICE, now=NOW)


def test_sign_formats_differ_by_prepare_id() -> None:
    a = sign_prepare("1", "2", "k", "m", "100", "0", "t")
    b = sign_complete("1", "2", "k", "m", "5", "100", "1", "t")
    assert a != b and len(a) == 32


def test_prepare_success_then_idempotent() -> None:
    inv = invoice()
    assert run(prepare_req(inv), inv).error is ClickError.SUCCESS
    assert inv.status is InvoiceStatus.PREPARED and inv.click_trans_id == "100"
    assert run(prepare_req(inv), inv).error is ClickError.SUCCESS


def test_prepare_other_click_transaction_rejected() -> None:
    inv = invoice()
    run(prepare_req(inv), inv)
    assert run(prepare_req(inv, trans="101"), inv).error is ClickError.UPDATE_FAILED


def test_bad_sign() -> None:
    inv = invoice()
    assert run(prepare_req(inv, secret="wrong"), inv).error is ClickError.SIGN_CHECK_FAILED


def test_wrong_service_id_is_sign_failure() -> None:
    inv = invoice()
    out = handle_click(prepare_req(inv), inv, secret=SECRET, service_id="1", now=NOW)
    assert out.error is ClickError.SIGN_CHECK_FAILED


def test_amount_mismatch() -> None:
    inv = invoice()
    assert run(prepare_req(inv, amount="1000.00"), inv).error is ClickError.INCORRECT_AMOUNT


def test_action_not_found() -> None:
    inv = invoice()
    assert run(prepare_req(inv, action="5"), inv).error is ClickError.ACTION_NOT_FOUND


def test_invoice_missing() -> None:
    inv = invoice()
    assert run(prepare_req(inv), None).error is ClickError.USER_NOT_FOUND


def test_complete_pays_once() -> None:
    inv = invoice()
    run(prepare_req(inv), inv)
    first = run(complete_req(inv), inv)
    assert first.error is ClickError.SUCCESS and first.paid
    assert inv.status is InvoiceStatus.PAID and inv.paid_at == NOW
    again = run(complete_req(inv), inv)
    assert again.error is ClickError.ALREADY_PAID and not again.paid


def test_complete_without_prepare() -> None:
    inv = invoice()
    assert run(complete_req(inv), inv).error is ClickError.TRANSACTION_NOT_FOUND


def test_complete_wrong_prepare_id() -> None:
    inv = invoice()
    run(prepare_req(inv), inv)
    assert run(complete_req(inv, prepare_id="7"), inv).error is ClickError.TRANSACTION_NOT_FOUND


def test_complete_error_cancels() -> None:
    inv = invoice()
    run(prepare_req(inv), inv)
    out = run(complete_req(inv, error=-5017), inv)
    assert out.error is ClickError.TRANSACTION_CANCELED and not out.paid
    assert inv.status is InvoiceStatus.CANCELED
    assert run(complete_req(inv), inv).error is ClickError.TRANSACTION_CANCELED
    assert run(prepare_req(inv), inv).error is ClickError.TRANSACTION_CANCELED


def test_prepare_on_paid_invoice() -> None:
    inv = invoice(status=InvoiceStatus.PAID)
    assert run(prepare_req(inv), inv).error is ClickError.ALREADY_PAID


def test_missing_params_is_bad_request() -> None:
    import pytest

    from app.shared.errors import ValidationFailed

    with pytest.raises(ValidationFailed):
        ClickRequest.parse({"click_trans_id": "1"})
