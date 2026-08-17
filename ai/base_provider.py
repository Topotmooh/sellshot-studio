"""AI-провайдеры для генерации фона."""
from __future__ import annotations

from pathlib import Path

from config import logger, settings


async def generate_background(
    width: int,
    height: int,
    category: str,
    style: str,
) -> Path | None:
    """
    Генерирует фон через AI.

    Возвращает путь к файлу фона или None
    (тогда будет использован локальный студийный фон).
    """
    if settings.AI_PROVIDER == "local":
        return None

    try:
        if settings.AI_PROVIDER == "yandex":
            from ai.yandex_provider import YandexArtProvider

            provider = YandexArtProvider()
        elif settings.AI_PROVIDER == "sber":
            logger.warning("Sber-провайдер пока не подключён, используем локальный фон")
            return None
        else:
            return None

        return await provider.generate(width, height, category, style)
    except Exception:
        logger.exception("Сбой AI-генерации фона, переключаемся на локальный фон")
        return None


async def generate_full_card(
    input_path: Path,
    output_path: Path,
    profile_key: str,
    category: str,
) -> Path | None:
    """Заглушка для будущей интеграции с внешними генераторами карточек."""
    logger.info("generate_full_card не реализован, используйте стандартный pipeline")
    return None