"""Тесты пайплайна без бота: вырезка + карточка + проверки профиля."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

from config import logger, settings
from core.profiles import PROFILES
from services import compositor, segmenter, storage

PHOTOS_DIR = Path("tests/photos")
REPORTS_DIR = Path("test_results")


async def process_one(photo_path: Path, profile) -> dict:
    started = time.perf_counter()

    # 1. Вырезание товара
    cutout_path = storage.new_temp_path(suffix=".png")
    await segmenter.cutout_product(photo_path, cutout_path)

    # 2. Сборка карточки
    result_path = storage.new_result_path(suffix=".jpg")
    await compositor.compose_card(cutout_path, result_path, profile, "other")

    elapsed = time.perf_counter() - started

    # 3. Проверки под профиль
    with Image.open(result_path) as img:
        width, height = img.size
        fmt = img.format

    weight_kb = result_path.stat().st_size / 1024

    checks = {
        "Точный размер под профиль": (
            width == profile.output_width and height == profile.output_height
        ),
        "Минимальная ширина": width >= profile.min_width,
        "Формат JPEG": fmt == profile.image_format,
        "Вес в лимите": weight_kb <= profile.max_file_size_mb * 1024,
    }

    return {
        "photo": photo_path.name,
        "profile": profile.key,
        "width": width,
        "height": height,
        "weight_kb": weight_kb,
        "time": elapsed,
        "checks": checks,
        "passed": all(checks.values()),
        "result": result_path,
    }


async def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    photos = (
        sorted(
            p for p in PHOTOS_DIR.iterdir()
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        )
        if PHOTOS_DIR.exists()
        else []
    )

    if not photos:
        print(f"❌ Нет фото в папке {PHOTOS_DIR}. Положи туда 2-3 фото товара.")
        return

    profiles = [PROFILES[k] for k in settings.enabled_profiles_list if k in PROFILES]

    results = []
    for photo in photos:
        for profile in profiles:
            print(f"⏳ {photo.name} -> {profile.key} ...")
            try:
                res = await process_one(photo, profile)
            except Exception as e:
                logger.exception("Ошибка теста")
                res = {
                    "photo": photo.name,
                    "profile": profile.key,
                    "passed": False,
                    "error": str(e),
                }
            results.append(res)
            print("   OK" if res.get("passed") else "   FAIL")

    # Отчёт
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"report_{stamp}.txt"

    lines = [
        "SELLSHOT STUDIO - PIPELINE TEST",
        f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        f"{'Фото':<20} {'Профиль':<12} {'Размер':<12} {'Вес KB':<9} {'Сек':<7} {'Статус':<6}",
    ]

    for r in results:
        if "error" in r:
            lines.append(
                f"{r['photo']:<20} {r['profile']:<12} {'ERROR':<12} {'-':<9} {'-':<7} {'FAIL':<6}"
            )
            continue
        lines.append(
            f"{r['photo']:<20} {r['profile']:<12} "
            f"{r['width']}x{r['height']:<7} {r['weight_kb']:<9.1f} {r['time']:<7.2f} "
            f"{'OK' if r['passed'] else 'FAIL':<6}"
        )

    lines += ["", "ДЕТАЛИ:", "=" * 70]
    for r in results:
        lines.append(f"{r['photo']} / {r['profile']}")
        if "error" in r:
            lines.append(f"  Ошибка: {r['error']}")
            continue
        for name, ok in r["checks"].items():
            lines.append(f"  {'[OK]' if ok else '[FAIL]'} {name}")
        lines.append(f"  Файл: {r['result']}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    total = len(results)
    ok_count = sum(1 for r in results if r.get("passed"))

    print()
    print("=" * 70)
    print(f"📄 Отчёт: {report_path}")
    print(f"📊 Всего: {total} | OK: {ok_count} | FAIL: {total - ok_count}")


if __name__ == "__main__":
    asyncio.run(main())