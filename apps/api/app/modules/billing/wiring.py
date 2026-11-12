from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.application.service import BillingService
from app.modules.billing.infrastructure.click import ClickShopProvider
from app.modules.billing.infrastructure.repositories import (
    SqlInvoiceRepository,
    SqlPlanRepository,
    SqlSubscriptionRepository,
)
from app.modules.billing.infrastructure.targets import IdentityGrantTargets
from app.modules.billing.settings import get_billing_settings
from app.shared.db import get_session, get_sessionmaker
from app.shared.entitlements import Entitlements, set_entitlements


def build_billing_service(session: AsyncSession) -> BillingService:
    s = get_billing_settings()
    return BillingService(
        session,
        SqlPlanRepository(session),
        SqlSubscriptionRepository(session),
        SqlInvoiceRepository(session),
        ClickShopProvider(s),
        s,
        IdentityGrantTargets(session),
    )


async def get_billing_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BillingService:
    return build_billing_service(session)


BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]


class SqlEntitlements:
    """EntitlementsPort implementation: reads plan data, never hardcodes tiers."""

    async def for_user(self, user_id: UUID) -> Entitlements:
        async with get_sessionmaker()() as session:
            return (await build_billing_service(session).my_billing(user_id)).entitlements


set_entitlements(SqlEntitlements())
