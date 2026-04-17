from aiogram import Dispatcher


def register_handlers(dispatcher: Dispatcher) -> None:
    from src.controllers.bot.routers import default, user

    dispatcher.include_routers(
        user.register_sub_routers(),
        default.router,
    )