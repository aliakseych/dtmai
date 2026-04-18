from src.controllers.bot.routers.user.bank.handlers import (  # noqa — registers handlers
    open_bank, select_subject, configure_filter, show_list, navigate_list, view_question,
)
from src.controllers.bot.routers.user.bank.router import register_filters as router