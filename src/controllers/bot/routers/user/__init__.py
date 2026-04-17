from aiogram import Router

router = Router(name="user")


def register_sub_routers() -> Router:
    from src.controllers.bot.routers.user import registration, menu, test, stats

    router.include_routers(
        registration.router(),
        menu.router(),
        test.router(),
        stats.router(),
    )

    return router