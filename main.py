"""SellShot Studio — точка входа."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import admin, category, photo, profile, start
from bot.middlewares.throttling import ThrottlingMiddleware
from config import logger, settings
from db import database as db
from services import storage


async def _cleanup_loop() -> None:
    """Фото пользователей удаляются каждые 6 часов (старше 24 ч)."""
    while True:
        await asyncio.sleep(6 * 3600)
        try:
            n = storage.cleanup_old_temp()
            if n:
                logger.info("🧹 Очистка: удалено старых файлов: %d", n)
        except Exception:
            logger.exception("Сбой автоочистки")


async def main() -> None:
    if not settings.BOT_TOKEN or ":" not in settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env")

    await db.init_db()

    bot_kwargs = {
        "token": settings.BOT_TOKEN,
        "default": DefaultBotProperties(parse_mode=ParseMode.HTML),
    }
    if settings.TELEGRAM_PROXY:
        bot_kwargs["proxy"] = settings.TELEGRAM_PROXY

    bot = Bot(**bot_kwargs)
    dp = Dispatcher()

    # Флуд-защита на все сообщения и callback'и
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(category.router)
    dp.include_router(photo.router)
    dp.include_router(admin.router)

    asyncio.create_task(_cleanup_loop())

    logger.info("🚀 Бот запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass