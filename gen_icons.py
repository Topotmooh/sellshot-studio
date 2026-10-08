"""Генерация иконок PWA для SellShot Studio."""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path("web/pwa/icons")
OUT.mkdir(parents=True, exist_ok=True)

BG = (255, 87, 34)
FG = (255, 255, 255)


def make(size: int, shrink: float = 1.0) -> Image.Image:
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)

    def X(v): return (0.5 + (v - 0.5) * shrink) * size
    def Y(v): return (0.5 + (v - 0.5) * shrink) * size

    d.rounded_rectangle(
        [X(0.40), Y(0.24), X(0.60), Y(0.36)],
        radius=int(size * 0.03), fill=FG
    )
    d.rounded_rectangle(
        [X(0.20), Y(0.32), X(0.80), Y(0.74)],
        radius=int(size * 0.06), fill=FG
    )
    cx, cy = X(0.50), Y(0.53)
    r1 = 0.14 * shrink * size
    r2 = 0.07 * shrink * size
    d.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], fill=BG)
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=FG)
    r3 = 0.025 * shrink * size
    fx, fy = X(0.70), Y(0.42)
    d.ellipse([fx - r3, fy - r3, fx + r3, fy + r3], fill=BG)
    return img


make(192).save(OUT / "icon-192.png")
make(512).save(OUT / "icon-512.png")
make(512, shrink=0.72).save(OUT / "icon-maskable-512.png")

print("OK: icons saved to", OUT.resolve())