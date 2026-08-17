"""SellShot Studio — конфигурация проекта."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ========== Telegram ==========
    BOT_TOKEN: str = ""
    ADMIN_ID: int | None = None
    # Прокси для Telegram (нужен только при запуске из РФ без VPN)
    # Примеры: http://user:pass@host:port или socks5://user:pass@host:port
    TELEGRAM_PROXY: str = ""

    # ========== App ==========
    APP_NAME: str = "SellShot Studio"
    DEBUG: bool = False

    # ========== Storage ==========
    DB_PATH: str = "data/app.db"
    TEMP_DIR: str = "data/temp"
    RESULTS_DIR: str = "data/results"
    ASSETS_DIR: str = "assets"
    BACKGROUNDS_DIR: str = "assets/backgrounds"

    # ========== Limits & watermark ==========
    FREE_DAILY_LIMIT: int = 5
    ENABLE_WATERMARK: bool = True
    WATERMARK_TEXT: str = "SellShot Studio"

    # ========== Processing ==========
    MAX_PHOTO_SIZE_MB: int = 20
    MAX_CONCURRENT_PROCESSING: int = 1
    PROCESSING_TIMEOUT_SECONDS: int = 120
    # Для VPS (2 vCPU) = 2, локально на N95 можно 4
    OMP_NUM_THREADS: int = 2

    # ========== Profiles ==========
    ENABLED_PROFILES: str = "universal,classifieds"
    DEFAULT_PROFILE: str = "universal"

    # ========== AI ==========
    # local | sber | yandex | aidentika
    AI_PROVIDER: str = "local"
    SBER_CLIENT_ID: str = Field(default="", repr=False)
    SBER_CLIENT_SECRET: str = Field(default="", repr=False)
    YANDEX_API_KEY: str = Field(default="", repr=False)
    YANDEX_FOLDER_ID: str = ""
    AIDENTIKA_API_KEY: str = Field(default="", repr=False)
    AIDENTIKA_CATEGORY_ID: str = "clothing"
    AIDENTIKA_CONCEPT_ID: str = "studio_catalog"

    # ========== Logging ==========
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"

    @property
    def enabled_profiles_list(self) -> list[str]:
        return [p.strip() for p in self.ENABLED_PROFILES.split(",") if p.strip()]

    @field_validator("ADMIN_ID", mode="before")
    @classmethod
    def validate_admin_id(cls, value):
        """Пустая строка в .env = None, а не ошибка."""
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("DEFAULT_PROFILE")
    @classmethod
    def validate_default_profile(cls, value: str) -> str:
        if value not in ("universal", "classifieds", "slonita"):
            raise ValueError(f"Неизвестный профиль: {value}")
        return value

    @field_validator("AI_PROVIDER")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        if value not in ("local", "sber", "yandex", "aidentika"):
            raise ValueError(f"Неизвестный AI-провайдер: {value}")
        return value


# Инициализация настроек
settings = Settings()

# Только CPU, без попыток использовать GPU
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", str(settings.OMP_NUM_THREADS))
os.environ.setdefault("ORT_LOGGING_LEVEL", "3")

# Создание рабочих директорий
for directory in (
    settings.TEMP_DIR,
    settings.RESULTS_DIR,
    settings.ASSETS_DIR,
    settings.BACKGROUNDS_DIR,
    Path(settings.DB_PATH).parent,
    Path(settings.LOG_FILE).parent,
):
    Path(directory).mkdir(parents=True, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("sellshot")
logger.info("✅ Конфигурация загружена: %s", settings.APP_NAME)

__all__ = ["settings", "logger"]