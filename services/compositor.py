"""Студийный композитинг в стиле Aidentika."""
from __future__ import annotations

import asyncio
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from config import logger
from core.profiles import CardProfile


# ================= ФОН =================

def _create_aidentika_background(width: int, height: int) -> Image.Image:
    """Студийный серый фон как у Aidentika: #d4d4d4 → #dfdfdf с градиентом."""
    bg = Image.new("RGB", (width, height), (212, 212, 212))
    draw = ImageDraw.Draw(bg)
    for y in range(height):
        shade = int(212 + 15 * (y / height))
        draw.line([(0, y), (width, y)], fill=(shade, shade, shade))
    return bg


def _create_background(width: int, height: int, style: str) -> Image.Image:
    """Выбор фона по стилю профиля."""
    if style == "white":
        return Image.new("RGB", (width, height), (255, 255, 255))
    return _create_aidentika_background(width, height)


def _fit_to_size(img: Image.Image, width: int, height: int) -> Image.Image:
    """Обрезает изображение точно под размер карточки (cover)."""
    ratio = max(width / img.width, height / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return img.crop((left, top, left + width, top + height))


# ================= МАСКА =================

def _remove_small_components(item: Image.Image) -> Image.Image:
    """
    Удаляет мелкие компоненты (полосы, дымка фона).
    Оставляет только самый большой компонент (товар).
    """
    arr = np.array(item.convert("RGBA"))
    alpha = arr[:, :, 3]

    # Бинаризация: всё, что alpha > 15, считаем частью маски
    mask = (alpha > 15).astype(np.uint8) * 255

    # Находим связные компоненты
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)

    if num_labels <= 1:
        return item

    # Находим самый большой компонент (кроме фона, label=0)
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_label = np.argmax(areas) + 1

    # Создаём маску только для самого большого компонента
    clean_mask = (labels == largest_label).astype(np.uint8) * 255

    # Применяем маску к альфа-каналу
    arr[:, :, 3] = clean_mask

    return Image.fromarray(arr, "RGBA")


def _clean_alpha(item: Image.Image) -> Image.Image:
    """
    Адаптивная очистка маски:
    - alpha > 60 → оставляем как есть
    - alpha 15-60 И яркость > 180 (белые манжеты) → восстанавливаем alpha=255
    - alpha 15-60 И яркость < 120 (тень/ореол) → удаляем (alpha=0)
    - alpha < 15 → удаляем
    """
    arr = np.array(item)  # RGBA
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    new_a = a.copy()
    mask_recover = (a >= 15) & (a <= 60) & (luminance > 180)
    mask_remove = (a >= 15) & (a <= 60) & (luminance <= 120)
    new_a[mask_recover] = 255
    new_a[mask_remove] = 0
    new_a[a < 15] = 0

    arr[:, :, 3] = new_a
    result = Image.fromarray(arr, "RGBA")

    return result.filter(ImageFilter.GaussianBlur(0.5))


def _tight_crop(item: Image.Image) -> Image.Image:
    """Обрезает пустые прозрачные поля вокруг товара."""
    bbox = item.split()[3].getbbox()
    return item.crop(bbox) if bbox else item


# ================= ЦВЕТ =================

def _color_grade(img: Image.Image) -> Image.Image:
    """Цветокоррекция: контраст + насыщенность + резкость как у Aidentika."""
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.15)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.08)
    img = ImageEnhance.Sharpness(img).enhance(1.25)
    return img


# ================= ТЕНИ =================

def _create_soft_shadow(item: Image.Image, width: int, height: int) -> Image.Image:
    """Мягкая студийная тень под товаром (Aidentika-style)."""
    alpha = item.split()[3]
    w, h = item.size

    shadow = alpha.filter(ImageFilter.GaussianBlur(max(int(w * 0.04), 12)))
    shadow = shadow.point(lambda v: int(v * 0.25))

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    x = (width - w) // 2
    y = (height - h) // 2 + int(h * 0.35)

    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    shadow_rgba = Image.merge(
        "RGBA", (black.split()[0], black.split()[1], black.split()[2], shadow)
    )
    canvas.paste(shadow_rgba, (x, y), shadow_rgba)
    return canvas


# ================= СБОРКА =================

def compose_sync(
    cutout_path: Path,
    output_path: Path,
    profile: CardProfile,
    category: str,
    background_path: Path | None = None,
) -> Path:
    """Собирает готовую карточку в стиле Aidentika (синхронно)."""
    with Image.open(cutout_path) as raw:
        item = raw.convert("RGBA")

        # 1. Удаляем мелкие компоненты (полосы, дымка)
        item = _remove_small_components(item)

        # 2. Адаптивная очистка маски
        item = _clean_alpha(item)

        # 3. Обрезаем пустые поля
        item = _tight_crop(item)

        width = profile.output_width
        height = profile.output_height

        # Фон
        if background_path is not None and Path(background_path).exists():
            with Image.open(background_path) as bg_img:
                bg = _fit_to_size(bg_img.convert("RGB"), width, height)
            bg = bg.filter(ImageFilter.GaussianBlur(1.5))
        else:
            bg = _create_aidentika_background(width, height)

        # Товар: 80% высоты
        max_w = int(width * 0.78)
        max_h = int(height * 0.80)
        ratio = min(max_w / item.width, max_h / item.height)
        new_w = int(item.width * ratio)
        new_h = int(item.height * ratio)
        item_resized = item.resize((new_w, new_h), Image.Resampling.LANCZOS)

        x = (width - new_w) // 2
        y = (height - new_h) // 2 - int(height * 0.02)

        # 1. Мягкая тень
        shadow_layer = _create_soft_shadow(item_resized, width, height)
        bg = Image.alpha_composite(bg.convert("RGBA"), shadow_layer)

        # 2. Товар
        bg.paste(item_resized, (x, y), item_resized)

        # 3. Color grading
        result = bg.convert("RGB")
        result = _color_grade(result)

        # JPEG с контролем веса
        quality = profile.jpeg_quality
        limit = profile.max_file_size_mb * 1024 * 1024
        result.save(output_path, "JPEG", quality=quality, optimize=True)

        while output_path.stat().st_size > limit and quality > 60:
            quality -= 5
            result.save(output_path, "JPEG", quality=quality, optimize=True)

    logger.info("✅ Карточка собрана: %s", output_path)
    return output_path


def finalize_external_card(
    result_path: Path,
    output_path: Path,
    profile: CardProfile,
) -> Path:
    """Приводит готовую карточку из внешнего API к размеру и весу профиля."""
    with Image.open(result_path) as img:
        result = _fit_to_size(img.convert("RGB"), profile.output_width, profile.output_height)
        result = _color_grade(result)

        quality = profile.jpeg_quality
        limit = profile.max_file_size_mb * 1024 * 1024
        result.save(output_path, "JPEG", quality=quality, optimize=True)

        while output_path.stat().st_size > limit and quality > 60:
            quality -= 5
            result.save(output_path, "JPEG", quality=quality, optimize=True)

    logger.info("✅ Внешняя карточка приведена к профилю: %s", output_path)
    return output_path


async def compose_card(
    cutout_path: Path,
    output_path: Path,
    profile: CardProfile,
    category: str,
    background_path: Path | None = None,
) -> Path:
    """Собирает карточку без блокировки бота."""
    return await asyncio.to_thread(
        compose_sync,
        Path(cutout_path),
        Path(output_path),
        profile,
        category,
        background_path,
    )