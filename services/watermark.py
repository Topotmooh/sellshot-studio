"""Водяной знак для бесплатных карточек."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import logger


def _get_font(size: int):
    candidates = [
        "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def apply_watermark(image: Image.Image, text: str) -> Image.Image:
    """Полупрозрачный плиточный водяной знак по диагонали."""
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(base.width // 15, 20)
    font = _get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    step_x = text_w + base.width // 8
    step_y = text_h + base.height // 5

    y = -base.height
    while y < base.height * 2:
        x = -base.width
        while x < base.width * 2:
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 80))
            x += step_x
        y += step_y

    overlay = overlay.rotate(30, expand=False)
    return Image.alpha_composite(base, overlay)


def watermark_file(path: Path, text: str, quality: int = 88) -> None:
    """Накладывает водяной знак на JPEG-файл на месте."""
    with Image.open(path) as img:
        marked = apply_watermark(img, text)
        marked.convert("RGB").save(path, "JPEG", quality=quality, optimize=True)
    logger.info("💧 Водяной знак наложен: %s", path)