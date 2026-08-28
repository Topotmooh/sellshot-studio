"""Студийный композитинг в стиле Aidentika."""
from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from config import logger
from core.profiles import CardProfile


# ================= ФОН =================

def _create_aidentika_background(width: int, height: int) -> Image.Image:
    """Студийный серый фон как у Aidentika."""
    bg = Image.new("RGB", (width, height), (212, 212, 212))
    draw = ImageDraw.Draw(bg)
    for y in range(height):
        shade = int(212 + 15 * (y / height))
        draw.line([(0, y), (width, y)], fill=(shade, shade, shade))
    return bg


def _create_background(width: int, height: int, style: str) -> Image.Image:
    """Выбор фона по стилю."""
    if style == "white":
        return Image.new("RGB", (width, height), (255, 255, 255))
    if style == "beige":
        return Image.new("RGB", (width, height), (240, 235, 226))
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

def _clean_alpha(item: Image.Image) -> Image.Image:
    """
    Адаптивная очистка + аккуратный край:
    - уверенные пиксели (a>=100) → непрозрачные;
    - СВЕТЛЫЕ полупрозрачные (ручка, манжеты) → непрозрачные;
    - ТЁМНЫЕ полупрозрачные (тень, ореол) → удаляем;
    - эрозия 1px убирает тёмную кромку исходного фото;
    - сглаживание убирает «ступеньки» границы.
    """
    arr = np.array(item)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    new_a = a.copy()
    new_a[a >= 100] = 255
    rec = (a >= 40) & (a < 100) & (luminance > 150)   # светлая полупрозрачность → в товар
    rem = (a >= 15) & (a < 100) & (luminance <= 120)  # тёмная полупрозрачность → убрать
    new_a[rec] = 255
    new_a[rem] = 0
    new_a[a < 15] = 0

    a_img = Image.fromarray(new_a)
    a_img = a_img.filter(ImageFilter.MinFilter(3))       # −1px тёмного обода
    a_img = a_img.filter(ImageFilter.GaussianBlur(0.8))  # сглаживание края

    arr[:, :, 3] = np.array(a_img)
    return Image.fromarray(arr, "RGBA")


def _tight_crop(item: Image.Image) -> Image.Image:
    """Обрезает пустые прозрачные поля вокруг товара."""
    bbox = item.split()[3].getbbox()
    return item.crop(bbox) if bbox else item


# ================= ЦВЕТ =================

def _auto_expose(item: Image.Image) -> Image.Image:
    """
    Автоэкспозиция ГАММОЙ: поднимает тени, но почти не трогает света.
    Тёмные товары (сумка) высветляются, светлые детали (ручка) не пересвечиваются.
    """
    arr = np.array(item.convert("RGBA"))
    a = arr[..., 3]
    m = a > 128
    if m.sum() < 500:
        return item

    rgb = arr[..., :3].astype(np.float32) / 255.0
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[m].mean()

    if lum < 0.35:
        # тёмный товар: гамма поднимает тени, света остаются собой
        rgb = np.power(rgb, 0.75)
        # держим чёрный глубоким
        rgb = np.clip((rgb - 0.5) * 1.06 + 0.5, 0.0, 1.0)
    elif lum > 0.80:
        rgb = np.clip((rgb - 0.5) * 1.05 + 0.5, 0.0, 1.0)

    arr[..., :3] = (rgb * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def _color_grade(img: Image.Image) -> Image.Image:
    """Цветокоррекция: мягче резкость, чтобы не подчёркивать край."""
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Color(img).enhance(1.06)
    img = ImageEnhance.Sharpness(img).enhance(1.10)
    return img


# ================= ТЕНИ =================

def _create_soft_shadow(item: Image.Image, width: int, height: int) -> Image.Image:
    """Мягкая студийная тень под товаром (Aidentika-style)."""
    alpha = item.split()[3]
    w, h = item.size

    shadow = alpha.filter(ImageFilter.GaussianBlur(max(int(w * 0.04), 12)))
    shadow = shadow.point(lambda v: int(v * 0.25))  # opacity 25%

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
    background_style: str | None = None,
) -> Path:
    """Собирает готовую карточку в стиле Aidentika (синхронно)."""
    with Image.open(cutout_path) as raw:
        item = raw.convert("RGBA")
        item = _clean_alpha(item)
        item = _tight_crop(item)
        item = _auto_expose(item)

        width = profile.output_width
        height = profile.output_height

        # Фон: AI-сцена, выбранный стиль или студийный градиент
        if background_path is not None and Path(background_path).exists():
            with Image.open(background_path) as bg_img:
                bg = _fit_to_size(bg_img.convert("RGB"), width, height)
            bg = bg.filter(ImageFilter.GaussianBlur(1.5))
        else:
            style = background_style or (
                profile.background_styles[0] if profile.background_styles else "studio"
            )
            bg = _create_background(width, height, style)

        # Товар: 80% высоты
        max_w = int(width * 0.78)
        max_h = int(height * 0.80)
        ratio = min(max_w / item.width, max_h / item.height)
        new_w = int(item.width * ratio)
        new_h = int(item.height * ratio)
        item_resized = item.resize((new_w, new_h), Image.Resampling.LANCZOS)

        x = (width - new_w) // 2
        y = (height - new_h) // 2 - int(height * 0.02)  # чуть выше центра

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
    background_style: str | None = None,
) -> Path:
    """Собирает карточку без блокировки бота."""
    return await asyncio.to_thread(
        compose_sync,
        Path(cutout_path),
        Path(output_path),
        profile,
        category,
        background_path,
        background_style,
    )