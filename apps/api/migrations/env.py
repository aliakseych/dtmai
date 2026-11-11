"""Alembic async env: one branch + one Postgres schema per module.

CREATE SCHEMA lives in each module's first revision (nothing may run on the connection
before context.configure, or Alembic stops committing).
"""

import asyncio
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.bootstrap.registry  # noqa: F401  (imports every module's models)
from app.settings import get_settings
from app.shared.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata
# Add one entry per module (schema == module name).
SCHEMAS = {
    "identity",
    "shared",
    "catalog",
    "bank",
    "billing",
    "lyceums",
    "notify",
    "ai",
    "labeling",
    "learning",
    "assessment",
    "gamification",
}
SCHEMA_FILTER: str | None = context.get_x_argument(as_dictionary=True).get("schema")
VERSION_SCHEMA = "public"


def include_name(name: str | None, type_: str, parent_names: dict[str, Any]) -> bool:
    if type_ == "schema":
        return name in SCHEMAS
    return True


def include_object(obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any) -> bool:
    if SCHEMA_FILTER is None:
        return True
    table = obj if type_ == "table" else getattr(obj, "table", None)
    return bool(table is None or table.schema == SCHEMA_FILTER)


def _url() -> str:
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def _configure(**kwargs: Any) -> None:
    context.configure(
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        include_object=include_object,
        version_table_schema=VERSION_SCHEMA,
        compare_type=True,
        **kwargs,
    )


def run_offline() -> None:
    _configure(url=_url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def _do_run(connection: Connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _url()
    engine = async_engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with engine.connect() as conn:
        await conn.run_sync(_do_run)
    await engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    asyncio.run(run_online())
