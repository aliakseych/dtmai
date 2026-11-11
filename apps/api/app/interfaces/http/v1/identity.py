from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.http.v1.learning import StatsOut
from app.modules.identity.application.service import UNSET, TokenPair
from app.modules.identity.domain.models import User
from app.modules.identity.wiring import IdentityServiceDep
from app.modules.learning import facade as learning_facade
from app.shared.audit import audit_admin
from app.shared.db import get_session
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
    dream_lyceum_ids: list[UUID]
    education_language_id: UUID | None
    city: str | None
    subject_ids: list[UUID]


class MePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    locale: str | None = None
    dream_lyceum_ids: list[UUID] | None = Field(default=None, max_length=10)
    education_language_id: UUID | None = None
    city: str | None = Field(default=None, max_length=50)
    subject_ids: list[UUID] | None = Field(default=None, max_length=10)


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
        dream_lyceum_ids=list(u.dream_lyceum_ids),
        education_language_id=u.education_language_id,
        city=u.city,
        subject_ids=list(u.subject_ids),
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
        dream_lyceum_ids=(body.dream_lyceum_ids or []) if "dream_lyceum_ids" in sent else UNSET,
        education_language_id=(
            body.education_language_id if "education_language_id" in sent else UNSET
        ),
        city=body.city if "city" in sent else UNSET,
        subject_ids=(body.subject_ids or []) if "subject_ids" in sent else UNSET,
    )
    return _me(updated)


# --- admin -------------------------------------------------------------------
class AdminUserOut(BaseModel):
    id: UUID
    email: str | None
    telegram_username: str | None
    display_name: str
    roles: list[str]
    status: Literal["active", "disabled"]
    is_system: bool
    created_at: datetime | None
    last_seen_at: datetime | None


class AdminUsersPage(BaseModel):
    total: int
    items: list[AdminUserOut]


class AdminUserPatch(BaseModel):
    roles: list[str] | None = Field(default=None, min_length=1)
    status: Literal["active", "disabled"] | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=200)


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=200)
    roles: list[str] = Field(min_length=1)


class AdminPasswordIn(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class LabelerCreate(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)


class LabelerCreated(BaseModel):
    id: UUID
    login: str
    password: str = Field(description="Shown once; not retrievable later")


def _admin_user(u: User) -> AdminUserOut:
    return AdminUserOut(
        id=u.id,
        email=u.email,
        telegram_username=u.telegram_username,
        display_name=u.name,
        roles=sorted(r.value for r in u.roles),
        status="disabled" if u.disabled else "active",
        is_system=u.is_system,
        created_at=u.created_at,
        last_seen_at=u.last_seen_at,
    )


@admin_router.get("", operation_id="identity_admin_list_users", responses=ERR)
async def admin_list_users(
    svc: IdentityServiceDep,
    who: Admin,
    q: str | None = None,
    role: str | None = None,
    status: Literal["active", "disabled"] | None = None,
    sort: Literal["created_at", "last_seen_at", "email"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AdminUsersPage:
    total, users = await svc.list_users(q, role, status, sort, order == "desc", page, size)
    audit_admin(who, "users.list", q=q, role=role, status=status, page=page, size=size)
    return AdminUsersPage(total=total, items=[_admin_user(u) for u in users])


@admin_router.post("", status_code=201, operation_id="identity_admin_create_user", responses=ERR)
async def admin_create_user(body: AdminUserCreate, svc: IdentityServiceDep, who: Admin) -> AdminUserOut:
    """Create a verified staff account (admin, labeler, editor, lyceum_rep...)."""
    user = await svc.create_staff(body.email, body.password, body.display_name, body.roles)
    audit_admin(who, "users.create", target_id=str(user.id), roles=body.roles)
    return _admin_user(user)


@admin_router.get("/{user_id}", operation_id="identity_admin_get_user", responses=ERR)
async def admin_get_user(user_id: UUID, svc: IdentityServiceDep, who: Admin) -> AdminUserOut:
    audit_admin(who, "users.get", target_id=str(user_id))
    return _admin_user(await svc.get_me(user_id))


@admin_router.patch("/{user_id}", operation_id="identity_admin_update_user", responses=ERR)
async def admin_update_user(
    user_id: UUID, body: AdminUserPatch, svc: IdentityServiceDep, who: Admin
) -> AdminUserOut:
    user = await svc.update_user(
        who.user_id, user_id, roles=body.roles, status=body.status, display_name=body.display_name
    )
    audit_admin(
        who, "users.update", target_id=str(user_id), roles=body.roles, status=body.status,
        display_name=body.display_name,
    )
    return _admin_user(user)


@admin_router.post("/{user_id}/reset-password", status_code=204, operation_id="identity_admin_reset_password", responses=ERR)
async def admin_reset_password(
    user_id: UUID, body: AdminPasswordIn, svc: IdentityServiceDep, who: Admin
) -> Response:
    await svc.reset_user_password(user_id, body.password)
    audit_admin(who, "users.reset_password", target_id=str(user_id))
    return Response(status_code=204)


@admin_router.get("/{user_id}/stats", operation_id="identity_admin_user_stats", responses=ERR)
async def admin_user_stats(
    user_id: UUID, svc: IdentityServiceDep, who: Admin,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatsOut:
    await svc.get_me(user_id)  # 404 for unknown users
    audit_admin(who, "users.stats", target_id=str(user_id))
    return StatsOut.of(await learning_facade.user_stats(session, user_id))


labelers_router = APIRouter(tags=["identity-admin"])


@labelers_router.post("", status_code=201, operation_id="identity_admin_create_labeler", responses=ERR)
async def admin_create_labeler(body: LabelerCreate, svc: IdentityServiceDep, who: Admin) -> LabelerCreated:
    """Create a system labeler; the generated login/password are returned once."""
    user, login, password = await svc.create_labeler(body.display_name)
    audit_admin(who, "labelers.create", target_id=str(user.id))
    return LabelerCreated(id=user.id, login=login, password=password)
