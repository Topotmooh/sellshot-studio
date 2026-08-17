"""Лимиты и премиум-статус."""
from __future__ import annotations

from config import settings
from db import database as db


async def check_limit(telegram_id: int):
    """Возвращает (allowed, used, limit). Для premium limit=None."""
    await db.ensure_user(telegram_id)
    used = await db.count_today(telegram_id)

    if await db.is_premium(telegram_id):
        return True, used, None

    limit = settings.FREE_DAILY_LIMIT
    return used < limit, used, limit


async def is_premium_user(telegram_id: int) -> bool:
    await db.ensure_user(telegram_id)
    return await db.is_premium(telegram_id)


async def consume(telegram_id: int, profile: str, category: str, ai_used: bool) -> None:
    await db.ensure_user(telegram_id)
    await db.add_usage(telegram_id, profile, category, ai_used)