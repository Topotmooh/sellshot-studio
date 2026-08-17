"""Вырезание товара: BiRefNet (fallback u2net) + очистка маски по цвету фона."""
from __future__ import annotations

import asyncio
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from config import logger, settings

# BiRefNet — точные края, целые манжеты, без боковых полос.
# u2net — только как fallback, если BiRefNet недоступен.
MODEL_CANDIDATES = ("birefnet-general", "u2net")

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
    """
    Цветовой отпечаток фона: частые цвета НИЖНЕЙ полосы исходника (12%).
    Там та же простыня в том же освещении/тени, что и «хвост» под товаром.
    """
    H, W = orig.shape[:2]
    strip = orig[int(H * 0.88):, :]

    q = (strip // 32).astype(np.int64)
    keys = q[..., 0] * 64 + q[..., 1] * 8 + q[..., 2]
    vals, counts = np.unique(keys, return_counts=True)

    min_count = max(int(0.01 * strip.shape[0] * strip.shape[1]), 50)
    return set(vals[counts >= min_count].tolist())


def _mask_cleanup(png_bytes: bytes, orig_bytes: bytes | None = None) -> bytes:
    """
    Очистка маски:
    - opening срезает тонкие «антенны»;
    - самая большая компонента удаляет отдельные куски;
    - ниже линии подола: пиксели цвета фона (простыни) удаляются;
    - жёсткий срез с допуском 1% как страховка.
    """
    arr = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    if arr is None or arr.ndim != 3 or arr.shape[2] < 4:
        return png_bytes

    orig = None
    if orig_bytes is not None:
        orig = cv2.imdecode(np.frombuffer(orig_bytes, np.uint8), cv2.IMREAD_COLOR)
        if orig is not None and orig.shape[:2] != arr.shape[:2]:
            orig = None

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
    bottom = None
    wide_rows = np.array([], dtype=np.int64)
    if max_span > 0:
        wide_rows = np.where(spans >= 0.6 * max_span)[0]
        if len(wide_rows):
            bottom = int(wide_rows[-1]) + max(int(0.01 * arr.shape[0]), 2)
            opened[bottom:, :] = 0

    # Возвращаем исходную альфу внутри восстановленной области
    dil = cv2.dilate(opened, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    arr[..., 3] = np.where(dil > 0, alpha, 0).astype(np.uint8)

    # Цветовое удаление «хвоста»: зона от 1% выше подола, всё что совпало с фоном
    if orig is not None and len(wide_rows):
        bg_keys = _background_color_keys(orig)
        if bg_keys:
            oq = (orig // 32).astype(np.int64)
            okeys = oq[..., 0] * 64 + oq[..., 1] * 8 + oq[..., 2]
            is_bg = np.isin(okeys, np.array(sorted(bg_keys), dtype=np.int64))

            zone = np.zeros(alpha.shape, dtype=bool)
            zs = max(int(wide_rows[-1]) - int(0.01 * arr.shape[0]), 0)
            zone[zs:, :] = True

            arr[..., 3] = np.where(zone & is_bg, 0, arr[..., 3])

    # Жёсткий срез ниже подола (страховка)
    if bottom is not None:
        arr[bottom:, :, 3] = 0

    ok, enc = cv2.imencode(".png", arr)
    return enc.tobytes() if ok else png_bytes


def _remove_sync(data: bytes) -> bytes:
    from rembg import remove

    best_bytes = None
    best_ratio = -1.0

    for model in MODEL_CANDIDATES:
        try:
            out = remove(data, session=_get_session(model))
        except Exception as e:
            logger.warning("⚠️ Модель %s недоступна: %s", model, e)
            continue

        ratio = _opaque_ratio(out)
        logger.info("🧠 Модель %s: маска %.1f%% кадра", model, ratio * 100)

        # Первая же модель с хорошей маской — в работу (BiRefNet)
        if ratio >= MIN_GOOD_MASK_RATIO:
            return _mask_cleanup(out, data)

        if ratio > best_ratio:
            best_ratio = ratio
            best_bytes = out

    if best_bytes is None:
        raise RuntimeError("Ни одна модель rembg не смогла вырезать товар")

    logger.warning("⚠️ Маска меньше порога (%.1f%%), беру лучшую", best_ratio * 100)
    return _mask_cleanup(best_bytes, data)


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