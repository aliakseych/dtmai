from aiogram import Router

router = Router(name="menu")


def register_filters() -> Router:
    from src.controllers.bot.filters.user_exists import UserExists
    router.message.filter(UserExists(exists=True))
    router.callback_query.filter(UserExists(exists=True))
    return router
