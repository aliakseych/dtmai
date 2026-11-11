"""City lookups exposed to other modules (identity validates `me.city` through this)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lyceums.infrastructure.repositories import SqlCities


def build_city_catalog(session: AsyncSession) -> SqlCities:
    return SqlCities(session)
