"""Вырезание товара: BiRefNet (CPU) + u2net-кроссчек + очистка маски."""
from __future__ import annotations

import asyncio
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from config import logger, settings

# Основные модели: первая доступная с хорошей маской — в работу.
# birefnet-general — проверенный рабочий для CPU (~60 сек).
# bria-rmbg (BRIA RMBG-2.0) на CPU слишком медленная (>120 сек) —
# вернём её основной на GPU в Фазе 2 (там 5–10 сек и идеальные края).
PRIMARY_MODELS = ("birefnet-general",)
# Кроссчек: u2net не видит «хвост» простыни → используем для его удаления.
CROSS_MODEL = "u2net"

MIN_GOOD_MASK_RATIO = 0.12

_sessions: dict = {}
_semaphore: asyncio.Semaphore | None = None


def _get_session(model: str):
    if model not in _sessions:
        from rembg import new_session

        logger.info("⏳ Загрузка модели rembg: %s (первый раз — скачивание)...", model)
        _sessions[model] = new_session(model)
        logger.info("✅ Модель rembg загружена: %s", model)
    return _sessions[model]


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_PROCESSING)
    return _semaphore


def _opaque_ratio(png_bytes: bytes) -> float:
    with Image.open(io.BytesIO(png_bytes)) as img:
        alpha = img.split()[-1]
        total = img.width * img.height
        opaque = alpha.point(lambda v: 255 if v > 60 else 0).histogram()[255]
        return opaque / total


def _background_color_keys(orig: np.ndarray) -> set:
    """Цветовой отпечаток фона: частые цвета нижней полосы исходника (12%)."""
    H, W = orig.shape[:2]
    strip = orig[int(H * 0.88):, :]

    q = (strip // 32).astype(np.int64)
    keys = q[..., 0] * 64 + q[..., 1] * 8 + q[..., 2]
    vals, counts = np.unique(keys, return_counts=True)

    min_count = max(int(0.01 * strip.shape[0] * strip.shape[1]), 50)
    return set(vals[counts >= min_count].tolist())


def _mask_cleanup(
    png_bytes: bytes,
    orig_bytes: bytes | None = None,
    cross_bytes: bytes | None = None,
) -> bytes:
    """
    Очистка маски:
    - opening + самая большая связная компонента;
    - «хвост» фона удаляется ТОЛЬКО при тройном совпадении:
      зона ниже подола + цвет фона + u2net пиксель не видит;
    - жёсткий срез — только если хвост реально обнаружен.
    """
    arr = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    if arr is None or arr.ndim != 3 or arr.shape[2] < 4:
        return png_bytes

    orig = None
    if orig_bytes is not None:
        orig = cv2.imdecode(np.frombuffer(orig_bytes, np.uint8), cv2.IMREAD_COLOR)
        if orig is not None and orig.shape[:2] != arr.shape[:2]:
            orig = None

    cross_alpha = None
    if cross_bytes is not None:
        cross = cv2.imdecode(np.frombuffer(cross_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
        if cross is not None and cross.shape[:2] == arr.shape[:2] and cross.ndim == 3:
            cross_alpha = cross[..., 3]

    alpha = arr[..., 3]

    mask = (alpha > 60).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Самая большая связная компонента
    n, labels, stats, _ = cv2.connectedComponentsWithStats(opened, 8)
    if n > 2:
        areas = stats[1:, cv2.CC_STAT_AREA]
        largest = int(np.argmax(areas)) + 1
        opened = np.where(labels == largest, 255, 0).astype(np.uint8)

    # Нижняя широкая линия товара (подол)
    spans = opened.sum(axis=1) / 255
    max_span = float(spans.max()) if spans.size else 0.0
    wide_rows = np.array([], dtype=np.int64)
    if max_span > 0:
        wide_rows = np.where(spans >= 0.6 * max_span)[0]

    # Возвращаем исходную альфу внутри восстановленной области
    dil = cv2.dilate(opened, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    arr[..., 3] = np.where(dil > 0, alpha, 0).astype(np.uint8)

    # Хвост фона: тройное условие + условный жёсткий срез
    if orig is not None and len(wide_rows):
        bg_keys = _background_color_keys(orig)
        if bg_keys:
            oq = (orig // 32).astype(np.int64)
            okeys = oq[..., 0] * 64 + oq[..., 1] * 8 + oq[..., 2]
            is_bg = np.isin(okeys, np.array(sorted(bg_keys), dtype=np.int64))

            zone = np.zeros(alpha.shape, dtype=bool)
            zone[int(wide_rows[-1]):, :] = True

            tail = zone & is_bg
            if cross_alpha is not None:
                tail = tail & (cross_alpha <= 60)

            removed = int(tail.sum())
            if removed:
                arr[..., 3] = np.where(tail, 0, arr[..., 3])
                logger.info("🧹 Хвост фона: удалено пикселей %d", removed)

            # Жёсткий срез — только если хвост действительно был
            if removed > int(0.005 * alpha.size):
                bottom = int(wide_rows[-1]) + max(int(0.01 * arr.shape[0]), 2)
                arr[bottom:, :, 3] = 0

    ok, enc = cv2.imencode(".png", arr)
    return enc.tobytes() if ok else png_bytes


def _remove_sync(data: bytes) -> bytes:
    from rembg import remove

    primary = None
    primary_name = None
    best_bytes = None
    best_ratio = -1.0

    for model in PRIMARY_MODELS:
        try:
            out = remove(data, session=_get_session(model))
        except Exception as e:
            logger.warning("⚠️ Модель %s недоступна: %s", model, e)
            continue

        ratio = _opaque_ratio(out)
        logger.info("🧠 Модель %s: маска %.1f%% кадра", model, ratio * 100)

        if ratio >= MIN_GOOD_MASK_RATIO:
            primary = out
            primary_name = model
            break

        if ratio > best_ratio:
            best_ratio = ratio
            best_bytes = out

    if primary is None:
        if best_bytes is None:
            raise RuntimeError("Ни одна модель rembg не смогла вырезать товар")
        logger.warning("⚠️ Маска меньше порога (%.1f%%), беру лучшую", best_ratio * 100)
        primary = best_bytes
        primary_name = "best-effort"

    # Кроссчек для удаления «хвоста» фона
    cross = None
    try:
        cross = remove(data, session=_get_session(CROSS_MODEL))
    except Exception as e:
        logger.warning("⚠️ Кроссчек %s недоступен: %s", CROSS_MODEL, e)

    logger.info("🧠 Primary-модель: %s", primary_name)
    return _mask_cleanup(primary, data, cross)


async def cutout_product(input_path: Path, output_path: Path) -> Path:
    """
    Вырезает товар с фона.

    input_path  — исходное фото (JPG)
    output_path — результат с прозрачным фоном (PNG)
    """
    data = await asyncio.to_thread(Path(input_path).read_bytes)

    async with _get_semaphore():
        result = await asyncio.wait_for(
            asyncio.to_thread(_remove_sync, data),
            timeout=settings.PROCESSING_TIMEOUT_SECONDS,
        )

    await asyncio.to_thread(Path(output_path).write_bytes, result)
    return output_path