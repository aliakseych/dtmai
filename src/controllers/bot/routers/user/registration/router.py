from aiogram import Router

router = Router(name="registration")


def register_filters() -> Router:
    # No UserExists filter — this router handles users who are NOT yet registered.
    # The /start command handler applies UserExists(exists=False) at handler level.
    return router