"""Генерация фона через Yandex ART (Yandex Cloud Foundation Models)."""
from __future__ import annotations

import asyncio
import base64
import time
from pathlib import Path

import aiohttp

from ai import prompt_builder
from config import logger, settings
from services import storage

API_BASE = "https://llm.api.cloud.yandex.net/foundationModels/v1"
TIMEOUT_SECONDS = 90
POLL_SECONDS = 3


class YandexArtProvider:
    name = "yandex"

    async def generate(
        self,
        width: int,
        height: int,
        category: str,
        style: str,
    ) -> Path | None:
        if not settings.YANDEX_API_KEY or not settings.YANDEX_FOLDER_ID:
            logger.warning("Ключи Yandex не заданы, используем локальный фон")
            return None

        prompt = prompt_builder.build_background_prompt(category, style)

        headers = {
            "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "modelUri": f"art://{settings.YANDEX_FOLDER_ID}/yandexart/latest",
            "messages": [{"role": "user", "text": prompt}],
            "generationOptions": {"numberOfImages": 1},
        }

        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Запуск генерации
            async with session.post(
                f"{API_BASE}/imageGenerationAsync",
                headers=headers,
                json=body,
            ) as resp:
                resp.raise_for_status()
                operation_id = (await resp.json())["id"]

            # Опрос готовности
            deadline = time.monotonic() + TIMEOUT_SECONDS

            while time.monotonic() < deadline:
                await asyncio.sleep(POLL_SECONDS)

                async with session.get(
                    f"{API_BASE}/imageGenerationAsync/{operation_id}",
                    headers=headers,
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

                status = data.get("status", "")

                if status in ("DONE", "PROCESSED"):
                    images = data.get("images", [])
                    if not images or "base64Data" not in images[0]:
                        logger.error("Yandex ART: пустой ответ")
                        return None

                    raw = base64.b64decode(images[0]["base64Data"])
                    out = storage.new_temp_path(suffix=".jpg")
                    await asyncio.to_thread(out.write_bytes, raw)
                    logger.info("✅ AI-фон сгенерирован (Yandex ART)")
                    return out

                if status == "ERROR":
                    logger.error("Yandex ART ошибка: %s", data)
                    return None

        logger.error("Yandex ART: таймаут генерации")
        return None