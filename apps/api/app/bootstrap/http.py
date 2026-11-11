from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.registry import MODULES
from app.interfaces.bot.webhook import router as tg_router
from app.settings import get_settings
from app.shared.errors import install_error_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    settings.assert_production_safe()
    app = FastAPI(title="DTM AI API", version="0.1.0", docs_url="/docs" if settings.env != "prod" else None)
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
