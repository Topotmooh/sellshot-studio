"""SQLite: пользователи, использование, платежи, паспорт продавца. Только ?-плейсхолдеры."""
from __future__ import annotations

from datetime import datetime, timedelta

import aiosqlite

from config import settings

DB_PATH = settings.DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id   INTEGER PRIMARY KEY,
                is_premium    INTEGER NOT NULL DEFAULT 0,
                premium_until TEXT,
                ai_trial_used INTEGER NOT NULL DEFAULT 0,
                consent_at    TEXT,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                profile     TEXT NOT NULL,
                category    TEXT NOT NULL,
                ai_used     INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS payments (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id    INTEGER NOT NULL,
                tariff         TEXT NOT NULL,
                amount_kopecks INTEGER NOT NULL,
                status         TEXT NOT NULL DEFAULT 'pending',
                created_at     TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS seller_passport (
                telegram_id INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                status      TEXT NOT NULL,
                city        TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );
            """
        )
        # Миграция: у старых БД может не быть consent_at
        try:
            await db.execute("ALTER TABLE users ADD COLUMN consent_at TEXT")
        except aiosqlite.OperationalError:
            pass
        await db.commit()


async def ensure_user(telegram_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, created_at) VALUES (?, ?)",
            (telegram_id, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def is_premium(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT is_premium, premium_until FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ) as cur:
            row = await cur.fetchone()

    if row is None:
        return False
    if not row["is_premium"]:
        return False
    until = row["premium_until"]
    if until is None:
        return True
    return datetime.fromisoformat(until) > datetime.utcnow()


async def set_premium(telegram_id: int, days: int = 30) -> None:
    await ensure_user(telegram_id)
    until = datetime.utcnow() + timedelta(days=days)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_premium = 1, premium_until = ? WHERE telegram_id = ?",
            (until.isoformat(), telegram_id),
        )
        await db.commit()


# ========== Согласие (152-ФЗ) ==========

async def set_consent(telegram_id: int) -> None:
    await ensure_user(telegram_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET consent_at = ? WHERE telegram_id = ?",
            (datetime.utcnow().isoformat(), telegram_id),
        )
        await db.commit()


async def get_consent(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT consent_at FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


# ========== Паспорт продавца (289-ФЗ) ==========

async def save_passport(telegram_id: int, name: str, status: str, city: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO seller_passport (telegram_id, name, status, city, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET name=excluded.name, "
            "status=excluded.status, city=excluded.city, updated_at=excluded.updated_at",
            (telegram_id, name, status, city, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_passport(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, status, city FROM seller_passport WHERE telegram_id = ?",
            (telegram_id,),
        ) as cur:
            return await cur.fetchone()


async def forget_user(telegram_id: int) -> None:
    """Право на забвение: удаляем паспорт и отзываем согласие."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM seller_passport WHERE telegram_id = ?", (telegram_id,))
        await db.execute("UPDATE users SET consent_at = NULL WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


# ========== Использование ==========

async def add_usage(telegram_id: int, profile: str, category: str, ai_used: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_events (telegram_id, profile, category, ai_used, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (telegram_id, profile, category, int(ai_used), datetime.utcnow().isoformat()),
        )
        await db.commit()


async def count_today(telegram_id: int) -> int:
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM usage_events WHERE telegram_id = ? AND created_at >= ?",
            (telegram_id, start.isoformat()),
        ) as cur:
            row = await cur.fetchone()
    return int(row[0]) if row else 0


async def stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM usage_events") as cur:
            events = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as cur:
            premium = (await cur.fetchone())[0]
    return {"users": users, "events": events, "premium": premium}