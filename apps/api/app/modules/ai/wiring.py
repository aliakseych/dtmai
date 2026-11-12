from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.modules.ai.application.explain import ExplainService
from app.modules.ai.application.gateway import AIGateway
from app.modules.ai.application.tutor import NoActiveMock, TutorService
from app.modules.ai.infrastructure.config import get_ai_settings
from app.modules.ai.infrastructure.openrouter import OpenRouterLLM
from app.modules.ai.infrastructure.repositories import (
    SqlAIConfigRepository,
    SqlLedgerRepository,
    SqlTutorSlotReservations,
)
from app.modules.ai.ports import ActiveMockChecker, AIConfigRepository, LedgerRepository, LLMPort
from app.shared.db import get_sessionmaker

_mock_checker: ActiveMockChecker = NoActiveMock()


def set_active_mock_checker(checker: ActiveMockChecker) -> None:
    """Called by the assessment module at import time."""
    global _mock_checker
    _mock_checker = checker


@lru_cache
def get_llm() -> LLMPort:
    return OpenRouterLLM(get_ai_settings())


def get_config_repo() -> AIConfigRepository:
    return SqlAIConfigRepository(get_sessionmaker())


def get_ledger_repo() -> LedgerRepository:
    return SqlLedgerRepository(get_sessionmaker())


def get_gateway() -> AIGateway:
    """Shared by labeling/ingestion (system calls) and the learner endpoints."""
    return AIGateway(get_llm(), get_config_repo(), get_ledger_repo())


GatewayDep = Annotated[AIGateway, Depends(get_gateway)]
ConfigRepoDep = Annotated[AIConfigRepository, Depends(get_config_repo)]
LedgerRepoDep = Annotated[LedgerRepository, Depends(get_ledger_repo)]


def get_explain_service(gw: GatewayDep) -> ExplainService:
    return ExplainService(gw, _mock_checker)


def get_tutor_service(gw: GatewayDep, ledger: LedgerRepoDep) -> TutorService:
    return TutorService(gw, ledger, _mock_checker, SqlTutorSlotReservations(get_sessionmaker()))


ExplainDep = Annotated[ExplainService, Depends(get_explain_service)]
TutorDep = Annotated[TutorService, Depends(get_tutor_service)]
