"""Конфигурация SellShot Studio."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Игнорирует лишние поля из .env
    )

    # ===== Telegram =====
    BOT_TOKEN: str = ""
    ADMIN_ID: Optional[int] = None
    ADMIN_USERNAME: str = "your_username"
    TELEGRAM_PROXY: Optional[str] = None

    # ===== Приложение =====
    APP_NAME: str = "SellShot Studio"
    DEBUG: bool = False

    # ===== AI =====
    AI_PROVIDER: str = "local"
    OMP_NUM_THREADS: int = 4
    MAX_CONCURRENT_PROCESSING: int = 1
    PROCESSING_TIMEOUT_SECONDS: int = 180

    # ===== Пути =====
    DB_PATH: str = "data/app.db"
    TEMP_DIR: str = "data/temp"
    RESULTS_DIR: str = "data/results"
    ASSETS_DIR: str = "assets"
    BACKGROUNDS_DIR: str = "assets/backgrounds"
    LOGS_DIR: str = "logs"

    # ===== Лимиты =====
    MAX_PHOTO_SIZE_MB: int = 20
    FREE_DAILY_LIMIT: int = 3

    # ===== Водяной знак =====
    ENABLE_WATERMARK: bool = True
    WATERMARK_TEXT: str = "SellShot Studio"

    # ===== Логирование =====
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"

    # ===== Платежи =====
    ENABLE_PAYMENTS: bool = False
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""

    # ===== Тарифы =====
    PRICE_PACK_10: int = 490
    PRICE_PACK_100: int = 1990
    PRICE_SUBSCRIPTION: int = 1490

    # ===== ВАЛИДАТОРЫ =====

    @field_validator("ADMIN_ID", mode="before")
    @classmethod
    def parse_admin_id(cls, v):
        """Пустая строка или None → None, иначе int."""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return int(v)


# ===== Инициализация =====

settings = Settings()


# ===== Логирование =====

def setup_logger() -> logging.Logger:
    """Настройка логгера."""
    logger = logging.getLogger("sellshot")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


# ===== Валидация =====

def validate_settings() -> None:
    """Проверяет критичные настройки."""
    if not settings.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен в .env")
        sys.exit(1)

    if settings.ADMIN_ID is None:
        logger.warning("⚠️ ADMIN_ID не установлен — админ-команды недоступны")

    for path_str in [
        settings.TEMP_DIR,
        settings.RESULTS_DIR,
        settings.ASSETS_DIR,
        settings.BACKGROUNDS_DIR,
        settings.LOGS_DIR,
    ]:
        Path(path_str).mkdir(parents=True, exist_ok=True)

    logger.info("✅ Настройки загружены: %s", settings.APP_NAME)
    logger.info("   AI Provider: %s", settings.AI_PROVIDER)
    logger.info("   Threads: %d", settings.OMP_NUM_THREADS)
    logger.info("   Watermark: %s", settings.ENABLE_WATERMARK)


validate_settings()