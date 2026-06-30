import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from bot.handlers import chat, matches, payment, profile, registration, search, shop, start
from bot.middlewares.db import DatabaseMiddleware
from config.settings import get_settings
from database.connections import Database

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    db = Database()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DatabaseMiddleware(db))

    @dp.errors()
    async def on_error(event: ErrorEvent) -> None:
        logger.exception("Handler xatosi: %s", event.exception)

    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(profile.router)
    dp.include_router(matches.router)
    dp.include_router(payment.router)
    dp.include_router(shop.router)
    dp.include_router(chat.router)
    dp.include_router(registration.router)

    await db.connect()
    logger.info("Bot ishga tushmoqda...")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
