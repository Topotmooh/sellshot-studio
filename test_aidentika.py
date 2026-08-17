"""Тест премиум-движка Aidentika без бота."""
import asyncio
from pathlib import Path

from ai.aidentika_provider import AidentikaProvider
from config import settings
from core.profiles import get_profile
from services import compositor, storage


async def main() -> None:
    photos_dir = Path("tests/photos")
    photos = sorted(photos_dir.glob("*.jpg")) + sorted(photos_dir.glob("*.jpeg"))
    if not photos:
        print("❌ Нет фото в tests/photos")
        return

    photo = photos[0]
    print(f"📸 Фото: {photo}")

    if not settings.AIDENTIKA_API_KEY:
        print("❌ AIDENTIKA_API_KEY не задан в .env")
        return

    provider = AidentikaProvider()

    print("⏳ Генерация через Aidentika (30–90 сек)...")
    result = await provider.generate_card(photo, "clothes")

    if result is None:
        print("❌ Генерация не удалась.")
        print("📋 Доступные категории Aidentika:")
        for cat in await provider.list_categories():
            print("  ", cat)
        print("Проверь AIDENTIKA_CATEGORY_ID / AIDENTIKA_CONCEPT_ID и баланс искр.")
        return

    profile = get_profile("universal")
    out = storage.new_result_path(suffix=".jpg")
    compositor.finalize_external_card(result, out, profile)
    storage.safe_unlink(result)

    print(f"✅ Готово: {out}")
    print("Сравни с примерами Aidentika и пришли скриншот.")


if __name__ == "__main__":
    asyncio.run(main())