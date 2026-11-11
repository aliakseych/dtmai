from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.identity.application.service import UNSET, TokenPair
from app.modules.identity.domain.models import User
from app.modules.identity.wiring import IdentityServiceDep
from app.shared.audit import audit_admin
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import ProblemDetails
from app.shared.security import Principal

router = APIRouter(tags=["identity"])
admin_router = APIRouter(tags=["identity-admin"])
Admin = Annotated[Principal, Depends(require_role("admin"))]

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    locale: str = "uz-Latn"


class EmailIn(BaseModel):
    email: EmailStr


class VerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class PasswordResetIn(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TelegramWebAppIn(BaseModel):
    init_data: str


class TelegramWidgetIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    auth_date: int
    hash: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MeOut(BaseModel):
    id: UUID
    email: str | None
    email_verified: bool
    telegram_id: int | None
    name: str
    locale: str
    roles: list[str]
    target_lyceum_id: UUID | None
    education_language_id: UUID | None


class MePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    locale: str | None = None
    target_lyceum_id: UUID | None = None
    education_language_id: UUID | None = None


def _tokens(t: TokenPair) -> TokensOut:
    return TokensOut(
        access_token=t.access_token, refresh_token=t.refresh_token, expires_in=t.expires_in
    )


def _me(u: User) -> MeOut:
    return MeOut(
        id=u.id,
        email=u.email,
        email_verified=u.email_verified,
        telegram_id=u.telegram_id,
        name=u.name,
        locale=u.locale,
        roles=sorted(r.value for r in u.roles),
        target_lyceum_id=u.target_lyceum_id,
        education_language_id=u.education_language_id,
    )


@router.post("/register", status_code=202, operation_id="identity_register", responses=ERR)
async def register(body: RegisterIn, svc: IdentityServiceDep) -> Response:
    await svc.register_email(body.email, body.password, body.name, body.locale)
    return Response(status_code=202)


@router.post("/email/resend", status_code=202, operation_id="identity_resend_code")
async def resend(body: EmailIn, svc: IdentityServiceDep) -> Response:
    await svc.resend_code(body.email)
    return Response(status_code=202)


@router.post("/email/verify", operation_id="identity_verify_email", responses=ERR)
async def verify(body: VerifyIn, svc: IdentityServiceDep) -> TokensOut:
    return _tokens(await svc.verify_email(body.email, body.code))


@router.post(
    "/password/forgot", status_code=202, operation_id="identity_password_forgot", responses=ERR
)
async def password_forgot(body: EmailIn, svc: IdentityServiceDep) -> Response:
    await svc.forgot_password(body.email)
    return Response(status_code=202)


@router.post("/password/reset", operation_id="identity_password_reset", responses=ERR)
async def password_reset(body: PasswordResetIn, svc: IdentityServiceDep) -> TokensOut:
    return _tokens(await svc.reset_password(body.email, body.code, body.password))


@router.post("/login", operation_id="identity_login", responses=ERR)
async def login(body: LoginIn, svc: IdentityServiceDep) -> TokensOut:
    return _tokens(await svc.login(body.email, body.password))


@router.post("/refresh", operation_id="identity_refresh", responses=ERR)
async def refresh(body: RefreshIn, svc: IdentityServiceDep) -> TokensOut:
    return _tokens(await svc.refresh(body.refresh_token))


@router.post("/logout", status_code=204, operation_id="identity_logout")
async def logout(body: RefreshIn, svc: IdentityServiceDep) -> Response:
    await svc.logout(body.refresh_token)
    return Response(status_code=204)


@router.post("/guest", operation_id="identity_guest", responses=ERR)
async def guest(svc: IdentityServiceDep) -> TokensOut:
    return _tokens(await svc.create_guest())


@router.post("/telegram/webapp", operation_id="identity_telegram_webapp", responses=ERR)
async def telegram_webapp(body: TelegramWebAppIn, svc: IdentityServiceDep) -> TokensOut:
    return _tokens(await svc.login_telegram_webapp(body.init_data))


@router.post("/telegram/widget", operation_id="identity_telegram_widget", responses=ERR)
async def telegram_widget(body: TelegramWidgetIn, svc: IdentityServiceDep) -> TokensOut:
    data = {k: str(v) for k, v in body.model_dump(exclude_none=True).items()}
    return _tokens(await svc.login_telegram_widget(data))


@router.get("/me", operation_id="identity_get_me", responses=ERR)
async def get_me(user: CurrentUser, svc: IdentityServiceDep) -> MeOut:
    return _me(await svc.get_me(user.user_id))


@router.patch("/me", operation_id="identity_update_me", responses=ERR)
async def patch_me(body: MePatch, user: CurrentUser, svc: IdentityServiceDep) -> MeOut:
    sent = body.model_fields_set
    updated = await svc.update_me(
        user.user_id,
        name=body.name,
        locale=body.locale,
        target_lyceum_id=body.target_lyceum_id if "target_lyceum_id" in sent else UNSET,
        education_language_id=(
            body.education_language_id if "education_language_id" in sent else UNSET
        ),
    )
    return _me(updated)


# --- admin -------------------------------------------------------------------
class AdminUserOut(BaseModel):
    id: UUID
    email: str | None
    name: str
    roles: list[str]
    created_at: datetime | None
    telegram_id: int | None = None


class AdminUsersPage(BaseModel):
    total: int
    items: list[AdminUserOut]


class RolesIn(BaseModel):
    roles: list[str] = Field(min_length=1)


def _admin_user(u: User) -> AdminUserOut:
    return AdminUserOut(
        id=u.id,
        email=u.email,
        name=u.name,
        roles=sorted(r.value for r in u.roles),
        created_at=u.created_at,
        telegram_id=u.telegram_id,
    )


@admin_router.get("", operation_id="identity_admin_list_users", responses=ERR)
async def admin_list_users(
    svc: IdentityServiceDep,
    who: Admin,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUsersPage:
    total, users = await svc.list_users(q, limit, offset)
    audit_admin(who, "users.list", q=q, limit=limit, offset=offset)
    return AdminUsersPage(total=total, items=[_admin_user(u) for u in users])


@admin_router.put("/{user_id}/roles", operation_id="identity_admin_set_roles", responses=ERR)
async def admin_set_roles(
    user_id: UUID, body: RolesIn, svc: IdentityServiceDep, who: Admin
) -> AdminUserOut:
    user = await svc.set_roles(who.user_id, user_id, body.roles)
    audit_admin(who, "users.set_roles", target_id=str(user_id), roles=body.roles)
    return _admin_user(user)
