from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.stats.callback import Stats
from src.controllers.bot.routers.user.stats.router import router
from src.controllers.bot.routers.user.stats.keyboard import stats as stats_kb
from src.controllers.bot.routers.user.stats.utils.stats import aggregate_attempts, build_stats_text
from src.controllers.bot.utilities import reply_edit

from aiogram.types import CallbackQuery


@router.callback_query(Stats.filter())
async def handle_stats(callback: CallbackQuery, container: Container) -> None:
    user = await container.users.get_by_telegram_id(callback.from_user.id)
    attempts = await container.attempts.get_by_user(user["id"])

    if not attempts:
        text = (
            "📊 <b>Статистика</b>\n\n"
            "Ты ещё не ответил ни на один вопрос.\n"
            "Пройди тест, чтобы здесь появилась статистика!"
        )
        await reply_edit.answer(callback, text=text, reply_markup=stats_kb.get(), parse_mode="HTML")
        return

    text = build_stats_text(aggregate_attempts(attempts))
    await reply_edit.answer(callback, text=text, reply_markup=stats_kb.get(), parse_mode="HTML")