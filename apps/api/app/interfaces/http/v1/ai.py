from dataclasses import asdict
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.application.errors import ensure_registered
from app.modules.ai.application.suggestions import suggest_for
from app.modules.ai.application.tutor import ChatTurn
from app.modules.ai.domain.budget import MICRO, Limits
from app.modules.ai.domain.routing import ModelRoute, Task
from app.modules.ai.wiring import ConfigRepoDep, ExplainDep, LedgerRepoDep, TutorDep
from app.shared.db import get_session
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import NotFound, ProblemDetails
from app.shared.security import Principal

router = APIRouter(tags=["ai"])
admin_router = APIRouter(tags=["ai-admin"])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden / not entitled"},
    404: {"model": ProblemDetails, "description": "Not found"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
    429: {"model": ProblemDetails, "description": "Limit reached"},
    502: {"model": ProblemDetails, "description": "AI upstream failed"},
    503: {"model": ProblemDetails, "description": "AI unavailable"},
}

SessionDep = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[Principal, Depends(require_role("admin"))]

Locale = Literal["uz-Latn", "uz-Cyrl", "ru", "en"]


class ExplainIn(BaseModel):
    locale: Locale = "uz-Latn"


class ExplainOut(BaseModel):
    question_id: UUID
    locale: str
    explanation: str
    cached: bool
    model: str | None


class TutorTurnIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class TutorIn(BaseModel):
    messages: list[TutorTurnIn] = Field(min_length=1, max_length=40)
    question_id: UUID | None = None
    locale: Locale = "uz-Latn"


class TutorQuizOut(BaseModel):
    """Inline quiz; the client checks `correct_index` itself."""

    stem: str
    options: list[str]
    correct_index: int
    explanation: str


class TutorQuotaOut(BaseModel):
    limit: int = Field(description="Messages per day; -1 = unlimited")
    used: int
    remaining: int = Field(description="-1 = unlimited")


class TutorOut(BaseModel):
    reply: str
    model: str
    quiz: TutorQuizOut | None = None
    quota: TutorQuotaOut


class TutorSuggestionsOut(BaseModel):
    suggestions: list[str]
    quota: TutorQuotaOut


@router.post("/explain/{question_id}", operation_id="ai_explain_question", responses=ERR)
async def explain(
    question_id: UUID,
    user: CurrentUser,
    svc: ExplainDep,
    session: SessionDep,
    body: ExplainIn | None = None,
) -> ExplainOut:
    locale = body.locale if body else "uz-Latn"
    text, cached, model = await svc.explain(session, user.user_id, question_id, locale)
    return ExplainOut(
        question_id=question_id, locale=locale, explanation=text, cached=cached, model=model
    )


@router.post("/tutor", operation_id="ai_tutor_chat", responses=ERR)
async def tutor(body: TutorIn, user: CurrentUser, svc: TutorDep, session: SessionDep) -> TutorOut:
    ensure_registered(user.roles)
    r = await svc.chat(
        session,
        user.user_id,
        [ChatTurn(m.role, m.content) for m in body.messages],
        question_id=body.question_id,
        locale=body.locale,
    )
    quiz = (
        TutorQuizOut(
            stem=r.quiz.stem,
            options=r.quiz.options,
            correct_index=r.quiz.correct_index,
            explanation=r.quiz.explanation,
        )
        if r.quiz
        else None
    )
    return TutorOut(reply=r.text, model=r.model, quiz=quiz, quota=TutorQuotaOut(**asdict(r.quota)))


@router.get("/tutor/suggestions", operation_id="ai_tutor_suggestions", responses=ERR)
async def tutor_suggestions(
    user: CurrentUser, svc: TutorDep, session: SessionDep, locale: Locale = "uz-Latn"
) -> TutorSuggestionsOut:
    """Prompt chips from the learner's weak topics, plus today's remaining quota."""
    ensure_registered(user.roles)
    return TutorSuggestionsOut(
        suggestions=await suggest_for(session, user.user_id, locale),
        quota=TutorQuotaOut(**asdict(await svc.quota(user.user_id))),
    )


# ---- admin: model routing, limits, spend ----------------------------------------------------


class RouteIO(BaseModel):
    task: Task
    slot: int = Field(ge=0, le=9, default=0)
    model: str = Field(min_length=1, max_length=120)
    temperature: float = Field(ge=0, le=2, default=0.2)
    max_tokens: int = Field(ge=16, le=32000, default=2048)
    price_in_usd_per_mtok: float = Field(ge=0, default=0)
    price_out_usd_per_mtok: float = Field(ge=0, default=0)
    enabled: bool = True


class LimitsIO(BaseModel):
    enabled: bool
    daily_spend_cap_usd: float = Field(ge=0, description="0 disables the cap")
    user_daily_token_budget: int = Field(ge=0, description="0 disables the cap")


class SpendRowOut(BaseModel):
    key: str
    calls: int
    tokens_in: int
    tokens_out: int
    cost_usd: float


class SpendReportOut(BaseModel):
    spent_today_usd: float
    daily_spend_cap_usd: float
    by_day: list[SpendRowOut]
    by_task: list[SpendRowOut]
    by_model: list[SpendRowOut]
    by_purpose: list[SpendRowOut]


def _route_out(r: ModelRoute) -> RouteIO:
    return RouteIO(
        task=r.task,
        slot=r.slot,
        model=r.model,
        temperature=r.temperature,
        max_tokens=r.max_tokens,
        price_in_usd_per_mtok=r.price_in_micro_per_mtok / MICRO,
        price_out_usd_per_mtok=r.price_out_micro_per_mtok / MICRO,
        enabled=r.enabled,
    )


@admin_router.get("/routes", operation_id="ai_admin_list_routes", responses=ERR)
async def list_routes(_: Admin, repo: ConfigRepoDep) -> list[RouteIO]:
    return [_route_out(r) for r in await repo.all_routes()]


@admin_router.put("/routes", operation_id="ai_admin_put_route", responses=ERR)
async def put_route(body: RouteIO, admin: Admin, repo: ConfigRepoDep) -> RouteIO:
    route = ModelRoute(
        task=body.task,
        slot=body.slot,
        model=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        price_in_micro_per_mtok=round(body.price_in_usd_per_mtok * MICRO),
        price_out_micro_per_mtok=round(body.price_out_usd_per_mtok * MICRO),
        enabled=body.enabled,
    )
    await repo.upsert_route(route, admin.user_id)
    return _route_out(route)


@admin_router.delete(
    "/routes/{task}/{slot}", status_code=204, operation_id="ai_admin_delete_route", responses=ERR
)
async def delete_route(task: Task, slot: int, _: Admin, repo: ConfigRepoDep) -> Response:
    if not await repo.delete_route(task, slot):
        raise NotFound("route not found")
    return Response(status_code=204)


@admin_router.get("/limits", operation_id="ai_admin_get_limits", responses=ERR)
async def get_limits(_: Admin, repo: ConfigRepoDep) -> LimitsIO:
    lim = await repo.limits()
    return LimitsIO(
        enabled=lim.enabled,
        daily_spend_cap_usd=lim.daily_spend_cap_micro / MICRO,
        user_daily_token_budget=lim.user_daily_token_budget,
    )


@admin_router.put("/limits", operation_id="ai_admin_put_limits", responses=ERR)
async def put_limits(body: LimitsIO, admin: Admin, repo: ConfigRepoDep) -> LimitsIO:
    await repo.set_limits(
        Limits(body.enabled, round(body.daily_spend_cap_usd * MICRO), body.user_daily_token_budget),
        admin.user_id,
    )
    return body


@admin_router.get("/spend", operation_id="ai_admin_spend", responses=ERR)
async def spend(
    _: Admin, repo: ConfigRepoDep, ledger: LedgerRepoDep, days: int = 7
) -> SpendReportOut:
    report = await ledger.spend_report(min(max(days, 1), 90))
    lim = await repo.limits()

    def rows(items: list[Any]) -> list[SpendRowOut]:
        return [
            SpendRowOut(
                key=r.key,
                calls=r.calls,
                tokens_in=r.tokens_in,
                tokens_out=r.tokens_out,
                cost_usd=r.cost_micro / MICRO,
            )
            for r in items
        ]

    return SpendReportOut(
        spent_today_usd=await ledger.spent_today_micro() / MICRO,
        daily_spend_cap_usd=lim.daily_spend_cap_micro / MICRO,
        by_day=rows(report.by_day),
        by_task=rows(report.by_task),
        by_model=rows(report.by_model),
        by_purpose=rows(report.by_purpose),
    )
