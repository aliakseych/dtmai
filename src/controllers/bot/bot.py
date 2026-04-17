from src.controllers.bot.container import Container
from src.controllers.bot.middlewares.error_handler import ErrorMiddleware
from src.controllers.bot.routers import register_handlers
from src.interfaces.mongodb.client import MongoClient
from src.settings import settings

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage


async def main() -> None:
    """Start the Telegram bot."""
    mongo = MongoClient(settings.MONGO_URI, settings.DB_NAME)
    container = Container(mongo)

    storage = MemoryStorage()  # swap for RedisStorage in production

    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.middleware(ErrorMiddleware())

    register_handlers(dispatcher)

    bot = Bot(token=settings.TELEGRAM_TOKEN)

    try:
        print("Started polling")
        await dispatcher.start_polling(bot, container=container)
    finally:
        await bot.session.close()
        print("Stopped polling")