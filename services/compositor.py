"""Композитинг: собирает карточку товара из вырезанного продукта и фона."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


async def compose_card(
    cutout_path: Path,
    output_path: Path,
    profile: dict,
    category: str = "universal",
    background: str = "white"  # ← НОВЫЙ ПАРАМЕТР
) -> Path:
    """
    Создаёт студийную карточку товара:
    1. Загружает вырезанный продукт (PNG с альфа-каналом)
    2. Загружает выбранный фон
    3. Размещает продукт по центру с тенью
    4. Сохраняет результат в output_path
    """
    
    # 1. Загружаем вырезанный продукт
    product = Image.open(cutout_path).convert("RGBA")
    
    # 2. Создаём фон 1080x1080
    bg_path = Path(__file__).parent.parent / "web" / "pwa" / "backgrounds" / f"{background}.jpg"
    
    if bg_path.exists():
        # Загружаем реальный фон
        bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.LANCZOS)
    else:
        # Фоллбэк на белый фон
        bg = Image.new("RGB", (1080, 1080), (255, 255, 255))
    
    # 3. Масштабируем продукт (не более 80% от фона)
    max_size = int(1080 * 0.8)
    product.thumbnail((max_size, max_size), Image.LANCZOS)
    
    # 4. Создаём тень под продуктом
    shadow = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    pw, ph = product.size
    shadow_x = (1080 - pw) // 2
    shadow_y = (1080 - ph) // 2 + 20
    
    # Рисуем размытый эллипс-тень
    shadow_ellipse = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    se_draw = ImageDraw.Draw(shadow_ellipse)
    se_draw.ellipse(
        [shadow_x + 20, shadow_y + ph - 30, shadow_x + pw - 20, shadow_y + ph + 30],
        fill=(0, 0, 0, 60)
    )
    shadow_ellipse = shadow_ellipse.filter(ImageFilter.GaussianBlur(radius=15))
    
    # 5. Накладываем тень на фон
    bg.paste(shadow_ellipse, (0, 0), shadow_ellipse)
    
    # 6. Накладываем продукт по центру
    product_x = (1080 - pw) // 2
    product_y = (1080 - ph) // 2
    
    bg.paste(product, (product_x, product_y), product)
    
    # 7. Сохраняем результат
    bg.save(output_path, "JPEG", quality=95)
    
    return output_path