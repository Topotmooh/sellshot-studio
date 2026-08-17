"""Админ-команды. Доступны ТОЛЬКО ADMIN_ID."""
from __future__ import annotations

from aiogram import F, Router, types

from config import logger, settings
from db import database as db

router = Router()


def _is_admin(user_id: int) -> bool:
    return settings.ADMIN_ID is not None and user_id == settings.ADMIN_ID


@router.message(F.text.startswith("/premium"))
async def premium_cmd(message: types.Message) -> None:
    if not _is_admin(message.from_user.id):
        logger.warning("🛡 Попытка /premium от не-админа: %s", message.from_user.id)
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("Формат: /premium <user_id> [дней]")
        return

    user_id = int(parts[1])
    days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 30
    await db.set_premium(user_id, days)
    await message.answer(f"✅ Выдан премиум {user_id} на {days} дн.")


@router.message(F.text == "/stats")
async def stats_cmd(message: types.Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    s = await db.stats()
    await message.answer(
        f"📊 Статистика:\n"
        f"Пользователей: {s['users']}\n"
        f"Карточек сделано: {s['events']}\n"
        f"Премиум: {s['premium']}"
    )