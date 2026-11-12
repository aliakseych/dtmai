from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.registry import MODULES
from app.interfaces.bot.webhook import router as tg_router
from app.settings import get_settings
from app.shared.errors import UnhandledErrorMiddleware, install_error_handlers
from app.shared.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    settings.assert_production_safe()
    configure_logging(settings)
    prod = settings.env == "prod"
    # Offline export (scripts/export_openapi.py -> app.openapi()) does not need the served schema.
    app = FastAPI(
        title="DTM AI API",
        version="0.1.0",
        docs_url=None if prod else "/docs",
        redoc_url=None if prod else "/redoc",
        openapi_url=None if prod else "/openapi.json",
    )
    app.add_middleware(UnhandledErrorMiddleware)  # inner to CORS: 500s keep CORS headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    for router, prefix in MODULES:
        app.include_router(router, prefix=f"/v1{prefix}")
    app.include_router(tg_router)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
