from fastapi import APIRouter

from app.interfaces.http.v1 import ai, assessment, bank, billing, catalog, gamification, identity, ingestion, labeling, learning, media, lyceums, notify
import app.modules.lyceums.facade  # noqa: F401  (plugs LyceumBenchmark into assessment)

# One line per module: (router, prefix). Importing a router also imports its ORM models,
# which registers them on Base.metadata for Alembic.
MODULES: list[tuple[APIRouter, str]] = [
    (identity.router, "/identity"),
    (catalog.router, "/catalog"),
    (catalog.admin_router, "/admin/catalog"),
    (bank.router, "/bank"),
    (bank.admin_router, "/admin/bank"),
    (billing.router, "/billing"),
    (billing.admin_router, "/admin/billing"),
    (lyceums.router, "/lyceums"),
    (lyceums.admin_router, "/admin/lyceums"),
    (notify.router, "/notify"),
    (learning.router, "/learning"),
    (assessment.router, "/assessment"),
    (gamification.router, "/gamification"),
    (gamification.me_router, "/me"),
    (gamification.admin_router, "/admin/gamification"),
    (identity.admin_router, "/admin/users"),
    (identity.labelers_router, "/admin/labelers"),
    (media.admin_router, "/admin/media"),
    (notify.admin_router, "/admin/notifications"),
    (ai.router, "/ai"),
    (ai.admin_router, "/admin/ai"),
    (labeling.router, "/labeling"),
    (labeling.admin_router, "/admin/labeling"),
    (ingestion.admin_router, "/admin/ingestion"),
]

# Modules exposing taskiq tasks (dotted import paths).
TASK_MODULES: list[str] = [
    "app.interfaces.jobs.identity",
    "app.interfaces.jobs.lyceums",
    "app.interfaces.jobs.notify",
    "app.modules.labeling.tasks",
    "app.interfaces.jobs.gamification",
    "app.interfaces.jobs.assessment",
]
