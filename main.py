"""SellShot Studio — главный файл запуска бота."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings, logger
from bot.handlers import start, photo


def resolve_proxy():
    """Определяет прокси: Karing по умолчанию, 'direct' = без прокси."""
    proxy = (settings.TELEGRAM_PROXY or "").strip()

    # Пусто или заглушка -> Karing
    if (not proxy) or ("NL_IP" in proxy):
        proxy = "http://127.0.0.1:3067"

    # Явное отключение
    if proxy.lower() in ("direct", "none", "off"):
        return None

    return proxy


async def main():
    """Запуск бота."""
    proxy = resolve_proxy()

    if proxy:
        logger.info("🔗 Используем прокси: %s", proxy)
        session = AiohttpSession(proxy=proxy)
    else:
        logger.info("🔗 Прямое подключение (без прокси)")
        session = AiohttpSession()

    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(photo.router)

    logger.info("🤖 Бот запущен: %s", settings.APP_NAME)
    logger.info("   Admin ID: %s", settings.ADMIN_ID)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            timeout=60,
        )
    except Exception as e:
        logger.error("❌ Ошибка polling: %s", e, exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")