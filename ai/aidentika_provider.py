"""Генерация карточек через Aidentika Public API (премиум-движок)."""
from __future__ import annotations

import asyncio
import base64
import time
import uuid
from pathlib import Path

import aiohttp
import filetype

from config import logger, settings

API_BASE = "https://api.aidentika.com/api/v1/public"


class AidentikaProvider:
    name = "aidentika"

    def __init__(self) -> None:
        self.api_key = settings.AIDENTIKA_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def list_categories(self) -> list:
        """Список категорий и концептов (подобрать правильные id)."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(f"{API_BASE}/categories", headers=self.headers) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
            return data if isinstance(data, list) else data.get("categories", [])
        except Exception as e:
            logger.warning("Aidentika categories: %s", e)
            return []

    async def generate_card(self, image_path: Path, category: str) -> Path | None:
        """Готовая карточка товара. Возвращает путь к файлу или None."""
        if not self.api_key:
            logger.warning("AIDENTIKA_API_KEY не задан")
            return None

        raw = Path(image_path).read_bytes()
        kind = filetype.guess(raw)
        mime = kind.mime if kind else "image/jpeg"

        body = {
            "images": [{"data": base64.b64encode(raw).decode(), "media_type": mime}],
            "category_id": settings.AIDENTIKA_CATEGORY_ID,
            "concept_id": settings.AIDENTIKA_CONCEPT_ID,
            "product_name": "Товар",
        }

        timeout = aiohttp.ClientTimeout(total=180)
        headers_json = {
            **self.headers,
            "Content-Type": "application/json",
            "Idempotency-Key": uuid.uuid4().hex,
        }

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 1. Запуск генерации
            async with session.post(
                f"{API_BASE}/generate/photo", headers=headers_json, json=body
            ) as resp:
                if resp.status not in (200, 201):
                    logger.error("Aidentika HTTP %s: %s", resp.status, await resp.text())
                    return None
                action_id = (await resp.json())["action_id"]

            logger.info("🤖 Aidentika: генерация %s запущена", action_id)

            # 2. Polling (первый запрос не раньше 20 сек)
            await asyncio.sleep(20)
            deadline = time.monotonic() + 120
            status = None

            while time.monotonic() < deadline:
                async with session.get(
                    f"{API_BASE}/status/{action_id}", headers=self.headers
                ) as resp:
                    status = await resp.json()

                if status.get("status") == "completed":
                    break
                if status.get("status") == "failed":
                    logger.error("Aidentika failed: %s", status.get("error_message"))
                    return None
                await asyncio.sleep(10)
            else:
                logger.error("Aidentika: таймаут генерации")
                return None

            # 3. Скачивание результата
            async with session.get(
                f"{API_BASE}/results/{action_id}/download",
                headers=self.headers,
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    logger.error("Aidentika download HTTP %s", resp.status)
                    return None
                result_raw = await resp.read()

        out = storage_new_temp_path()
        await asyncio.to_thread(out.write_bytes, result_raw)
        logger.info("✅ Aidentika: карточка готова (%s искр)", 4)
        return out


def storage_new_temp_path():
    from services import storage

    return storage.new_temp_path(suffix=".jpg")