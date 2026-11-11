from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.application.service import CatalogService
from app.modules.catalog.facade import service
from app.shared.db import get_session


async def get_catalog_service(session: Annotated[AsyncSession, Depends(get_session)]) -> CatalogService:
    return service(session)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
