import ipaddress
import json
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import AwareDatetime, BaseModel, Field

from app.modules.billing.domain.plans import GrantSource, Plan, Subscription
from app.modules.billing.settings import get_billing_settings
from app.modules.billing.wiring import BillingServiceDep
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import Forbidden, ProblemDetails

router = APIRouter(tags=["billing"])
admin_router = APIRouter(tags=["billing-admin"], dependencies=[Depends(require_role("admin"))])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}


class PlanOut(BaseModel):
    code: str
    names: dict[str, str]
    price_uzs: int
    period_months: int
    features: list[str]
    limits: dict[str, int]
    active: bool
    sort_order: int


class PlanIn(BaseModel):
    names: dict[str, str]
    price_uzs: int = Field(ge=0)
    period_months: int = 1
    features: list[str] = Field(default_factory=list)
    limits: dict[str, int] = Field(default_factory=dict)
    active: bool = True
    sort_order: int = 0


class PlanCreate(PlanIn):
    code: str = Field(min_length=1, max_length=40)


class PlanPatch(BaseModel):
    names: dict[str, str] | None = None
    price_uzs: int | None = Field(default=None, ge=0)
    period_months: int | None = None
    features: list[str] | None = None
    limits: dict[str, int] | None = None
    active: bool | None = None
    sort_order: int | None = None


class SubscriptionOut(BaseModel):
    id: UUID
    user_id: UUID
    plan_code: str
    status: str
    source: str
    started_at: datetime
    until: datetime


class EntitlementsOut(BaseModel):
    plan_code: str
    features: list[str]
    limits: dict[str, int]


class MyBillingOut(BaseModel):
    entitlements: EntitlementsOut
    subscription: SubscriptionOut | None
    payments_enabled: bool


class BillingConfigOut(BaseModel):
    payments_enabled: bool


class GrantIn(BaseModel):
    user_id: UUID
    plan_code: str
    months: int | None = Field(default=None, ge=1, le=36)
    until: AwareDatetime | None = None


class CheckoutIn(BaseModel):
    plan_code: str


class CheckoutOut(BaseModel):
    invoice_id: UUID
    amount_uzs: int
    pay_url: str


def _plan(p: Plan) -> PlanOut:
    return PlanOut(
        code=p.code,
        names=p.names,
        price_uzs=p.price_uzs,
        period_months=p.period_months,
        features=sorted(p.features),
        limits=p.limits,
        active=p.active,
        sort_order=p.sort_order,
    )


def _sub(s: Subscription) -> SubscriptionOut:
    return SubscriptionOut(
        id=s.id,
        user_id=s.user_id,
        plan_code=s.plan_code,
        status=s.status.value,
        source=s.source.value,
        started_at=s.started_at,
        until=s.until,
    )


# --- learner -----------------------------------------------------------------
@router.get("/plans", operation_id="billing_list_plans")
async def list_plans(svc: BillingServiceDep) -> list[PlanOut]:
    return [_plan(p) for p in await svc.list_plans(active_only=True)]


@router.get("/config", operation_id="billing_get_config")
async def get_config() -> BillingConfigOut:
    return BillingConfigOut(payments_enabled=get_billing_settings().payments_enabled)


@router.get("/me", operation_id="billing_get_me", responses=ERR)
async def get_me(user: CurrentUser, svc: BillingServiceDep) -> MyBillingOut:
    mine = await svc.my_billing(user.user_id)
    e = mine.entitlements
    return MyBillingOut(
        entitlements=EntitlementsOut(
            plan_code=e.plan_code, features=sorted(e.features), limits=e.limits
        ),
        subscription=_sub(mine.subscription) if mine.subscription else None,
        payments_enabled=get_billing_settings().payments_enabled,
    )


@router.post("/checkout", operation_id="billing_checkout", responses=ERR)
async def checkout(body: CheckoutIn, user: CurrentUser, svc: BillingServiceDep) -> CheckoutOut:
    invoice, url = await svc.checkout(user.user_id, body.plan_code, is_guest="guest" in user.roles)
    return CheckoutOut(invoice_id=invoice.id, amount_uzs=invoice.amount_uzs, pay_url=url)


# --- Click Shop callbacks (server-to-server) -----------------------------------
def _check_ip(request: Request) -> None:
    allowed = get_billing_settings().click_allowed_ips
    if not allowed:
        return
    host = request.client.host if request.client else ""
    try:
        addr = ipaddress.ip_address(host)
    except ValueError as e:
        raise Forbidden("ip not allowed", code="ip_not_allowed") from e
    if not any(addr in ipaddress.ip_network(n, strict=False) for n in allowed):
        raise Forbidden("ip not allowed", code="ip_not_allowed")


async def _click_params(request: Request) -> dict[str, str]:
    raw = await request.body()
    if "json" in request.headers.get("content-type", ""):
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            return {}
        return {k: str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    return dict(parse_qsl(raw.decode(errors="replace"), keep_blank_values=True))


_CLICK_BODY: dict[str, Any] = {
    "requestBody": {
        "required": True,
        "content": {"application/x-www-form-urlencoded": {"schema": {"type": "object"}}},
    }
}


@router.post(
    "/click/prepare", operation_id="billing_click_prepare", openapi_extra=_CLICK_BODY, responses=ERR
)
async def click_prepare(request: Request, svc: BillingServiceDep) -> dict[str, Any]:
    svc.ensure_payments_enabled()
    _check_ip(request)
    return await svc.process_click(await _click_params(request))


@router.post(
    "/click/complete",
    operation_id="billing_click_complete",
    openapi_extra=_CLICK_BODY,
    responses=ERR,
)
async def click_complete(request: Request, svc: BillingServiceDep) -> dict[str, Any]:
    svc.ensure_payments_enabled()
    _check_ip(request)
    return await svc.process_click(await _click_params(request))


# --- admin -------------------------------------------------------------------
@admin_router.get("/plans", operation_id="billing_admin_list_plans", responses=ERR)
async def admin_list_plans(svc: BillingServiceDep) -> list[PlanOut]:
    return [_plan(p) for p in await svc.list_plans(active_only=False)]


@admin_router.post(
    "/plans", status_code=201, operation_id="billing_admin_create_plan", responses=ERR
)
async def admin_create_plan(body: PlanCreate, svc: BillingServiceDep) -> PlanOut:
    plan = Plan(
        code=body.code,
        names=body.names,
        price_uzs=body.price_uzs,
        period_months=body.period_months,
        features=frozenset(body.features),
        limits=body.limits,
        active=body.active,
        sort_order=body.sort_order,
    )
    return _plan(await svc.create_plan(plan))


@admin_router.patch("/plans/{code}", operation_id="billing_admin_update_plan", responses=ERR)
async def admin_update_plan(code: str, body: PlanPatch, svc: BillingServiceDep) -> PlanOut:
    changes = body.model_dump(exclude_unset=True)
    if "features" in changes and changes["features"] is not None:
        changes["features"] = frozenset(changes["features"])
    changes = {k: v for k, v in changes.items() if v is not None}
    return _plan(await svc.update_plan(code, **changes))


@admin_router.delete(
    "/plans/{code}", status_code=204, operation_id="billing_admin_delete_plan", responses=ERR
)
async def admin_delete_plan(code: str, svc: BillingServiceDep) -> Response:
    await svc.delete_plan(code)
    return Response(status_code=204)


@admin_router.post("/grants", status_code=201, operation_id="billing_admin_grant", responses=ERR)
async def admin_grant(body: GrantIn, svc: BillingServiceDep) -> SubscriptionOut:
    sub = await svc.grant(
        body.user_id, body.plan_code, months=body.months, until=body.until, source=GrantSource.ADMIN
    )
    return _sub(sub)


@admin_router.post(
    "/subscriptions/{subscription_id}/revoke", operation_id="billing_admin_revoke", responses=ERR
)
async def admin_revoke(subscription_id: UUID, svc: BillingServiceDep) -> SubscriptionOut:
    return _sub(await svc.revoke(subscription_id))


@admin_router.get(
    "/users/{user_id}/subscriptions", operation_id="billing_admin_user_subscriptions", responses=ERR
)
async def admin_user_subscriptions(user_id: UUID, svc: BillingServiceDep) -> list[SubscriptionOut]:
    return [_sub(s) for s in await svc.user_subscriptions(user_id)]
