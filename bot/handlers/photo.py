"""Хендлеры обработки фото от пользователей."""
from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import logger, settings
from core.profiles import get_profile
from services.compositor import compose_card
from services.segmenter import cutout_product
from services.compliance import (
    generate_avito_description,
    generate_youla_description,
    generate_vk_description,
    generate_gde_description,
    generate_barahla_description,
    generate_kupipanda_description,
    generate_vkupiprodai_description,
    generate_yandex_description,
    generate_meshok_description,
    generate_looton_description,
)
from bot.webapp_url import get_web_app_url

router = Router()


# ===== ЛИМИТЫ =====

daily_usage: dict[int, dict] = {}


def get_daily_count(user_id: int) -> int:
    today = date.today().isoformat()
    user_data = daily_usage.get(user_id, {})
    if user_data.get("date") != today:
        daily_usage[user_id] = {"count": 0, "date": today}
        return 0
    return user_data.get("count", 0)


def increment_daily_count(user_id: int) -> int:
    today = date.today().isoformat()
    if user_id not in daily_usage or daily_usage[user_id]["date"] != today:
        daily_usage[user_id] = {"count": 0, "date": today}
    daily_usage[user_id]["count"] += 1
    return daily_usage[user_id]["count"]


# ===== ТЕКСТЫ =====

def generate_description_text(category: str = "universal") -> str:
    """Описание для Авито (основная площадка)."""
    templates = {
        "clothing": {
            "title": "Стильная одежда в отличном состоянии",
            "features": [
                "✅ Материал: высококачественная ткань",
                "✅ Размер: уточняйте в ЛС",
                "✅ Состояние: новое/отличное",
            ],
        },
        "shoes": {
            "title": "Обувь в отличном состоянии",
            "features": [
                "✅ Материал: натуральная кожа/экокожа",
                "✅ Размер: уточняйте в ЛС",
                "✅ Состояние: новое/отличное",
            ],
        },
        "bags": {
            "title": "Сумка стильная и вместительная",
            "features": [
                "✅ Материал: премиум экокожа",
                "✅ Размеры: уточняйте в ЛС",
                "✅ Состояние: новое/отличное",
            ],
        },
        "universal": {
            "title": "Товар в отличном состоянии",
            "features": [
                "✅ Качество: премиум",
                "✅ Состояние: новое/отличное",
                "✅ Комплектация: полная",
            ],
        },
    }

    tpl = templates.get(category, templates["universal"])

    return (
        f"🔥 {tpl['title']}\n\n"
        + "\n".join(tpl["features"])
        + f"\n\n{generate_avito_description()}\n\n"
        f"📞 Звоните или пишите в ЛС — отвечу быстро!"
    )


def get_platforms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Авито", callback_data="platform_avito"),
            InlineKeyboardButton(text="🔴 Юла", callback_data="platform_youla"),
        ],
        [
            InlineKeyboardButton(text="🔵 VK Маркет", callback_data="platform_vk"),
            InlineKeyboardButton(text="🟡 Яндекс", callback_data="platform_yandex"),
        ],
        [
            InlineKeyboardButton(text="🟢 gde.ru", callback_data="platform_gde"),
            InlineKeyboardButton(text="🟠 barahla", callback_data="platform_barahla"),
        ],
        [
            InlineKeyboardButton(text="🟣 kupipanda", callback_data="platform_kupipanda"),
            InlineKeyboardButton(text="🔵 vkupiprodai", callback_data="platform_vkupiprodai"),
        ],
        [
            InlineKeyboardButton(text="🟠 Мешок", callback_data="platform_meshok"),
            InlineKeyboardButton(text="🔴 Looton", callback_data="platform_looton"),
        ],
    ])


# ===== ХЕНДЛЕРЫ =====

@router.message(Command("photo"))
async def cmd_photo(message: Message):
    text = (
        "📸 <b>Загрузка фото для обработки:</b>\n\n"
        "1. Отправь мне фото товара (JPG/PNG до 20 МБ)\n"
        "2. Я обработаю его и создам студийную карточку\n"
        "3. Получи готовое фото + текст описания\n\n"
        f"🆓 Бесплатно: {settings.FREE_DAILY_LIMIT} карточек в день\n"
        f"💎 Пакет 10 карточек: {settings.PRICE_PACK_10} ₽\n\n"
        "Просто отправь фото — я всё сделаю сам!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(lambda m: m.photo and not m.text)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Селлер"

    daily_count = get_daily_count(user_id)
    if daily_count >= settings.FREE_DAILY_LIMIT:
        text = (
            f"⚠️ {user_name}, ты использовал все {settings.FREE_DAILY_LIMIT} "
            f"бесплатных карточек сегодня.\n\n"
            f"💎 Купи пакет 10 карточек за {settings.PRICE_PACK_10} ₽ — "
            f"и продолжай без ограничений!\n\n"
            f"Или открой Mini App 👇"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть Mini App",
                    web_app=WebAppInfo(url=get_web_app_url())
                )
            ],
            [
                InlineKeyboardButton(text="💎 Купить пакет", callback_data="buy_pack_10")
            ],
        ])
        await message.answer(text, reply_markup=keyboard)
        return

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)

    unique_id = uuid.uuid4().hex[:12]
    orig_path = Path(settings.TEMP_DIR) / f"{unique_id}_orig.jpg"
    cutout_path = Path(settings.TEMP_DIR) / f"{unique_id}_cutout.png"
    result_path = Path(settings.RESULTS_DIR) / f"{unique_id}_final.jpg"

    await message.bot.download_file(file.file_path, orig_path)
    logger.info("📥 Получено фото от %s: %s", user_id, orig_path.name)

    status_msg = await message.answer(
        "⏳ Обрабатываю фото...\n"
        "• Удаляю фон\n"
        "• Накладываю студийный свет\n"
        "• Добавляю тень\n\n"
        "Обычно занимает 30–60 секунд"
    )

    try:
        profile = get_profile("universal")

        await cutout_product(orig_path, cutout_path)
        await compose_card(
            cutout_path=cutout_path,
            output_path=result_path,
            profile=profile,
            category="universal",
        )

        new_count = increment_daily_count(user_id)

        caption = (
            f"✅ Готово, {user_name}!\n\n"
            f"📊 Использовано сегодня: {new_count}/{settings.FREE_DAILY_LIMIT}\n\n"
            f"📝 <b>Готовое описание для Авито:</b>\n"
            f"{generate_description_text()}\n\n"
            f"📱 Выбери площадку для публикации 👇"
        )

        photo_file = FSInputFile(result_path)
        await message.answer_photo(
            photo=photo_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_platforms_keyboard(),
        )
        logger.info("✅ Карточка создана для %s: %s", user_id, result_path.name)

    except Exception as e:
        logger.error("❌ Ошибка обработки для %s: %s", user_id, e, exc_info=True)
        await message.answer(
            f"😔 Ошибка при обработке фото.\n\n"
            f"Попробуй ещё раз или напиши админу: @{settings.ADMIN_USERNAME}"
        )

    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass
        for temp_file in [orig_path, cutout_path]:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass


# ===== КНОПКИ ПЛОЩАДОК =====

PLATFORM_DESCRIPTIONS = {
    "platform_avito": ("Авито", generate_avito_description),
    "platform_youla": ("Юла", generate_youla_description),
    "platform_vk": ("VK Маркет", generate_vk_description),
    "platform_yandex": ("Яндекс Объявления", generate_yandex_description),
    "platform_gde": ("gde.ru", generate_gde_description),
    "platform_barahla": ("barahla.net", generate_barahla_description),
    "platform_kupipanda": ("kupipanda.ru", generate_kupipanda_description),
    "platform_vkupiprodai": ("vkupiprodai.ru", generate_vkupiprodai_description),
    "platform_meshok": ("Мешок", generate_meshok_description),
    "platform_looton": ("Looton", generate_looton_description),
}


@router.callback_query(lambda c: c.data in PLATFORM_DESCRIPTIONS)
async def callback_platform(callback):
    platform_name, generator = PLATFORM_DESCRIPTIONS[callback.data]
    text = (
        f"📝 <b>Описание для {platform_name}:</b>\n\n"
        f"{generator()}\n\n"
        f"💡 Скопируй текст и вставь в объявление на {platform_name}."
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer(f"Описание для {platform_name} готово!")


@router.callback_query(lambda c: c.data == "noop")
async def callback_noop(callback):
    await callback.answer()


@router.callback_query(lambda c: c.data == "buy_pack_10")
async def callback_buy_pack(callback):
    text = (
        "💎 <b>Покупка пакета 10 карточек</b>\n\n"
        f"Стоимость: {settings.PRICE_PACK_10} ₽\n\n"
        f"Для оплаты переведи сумму на СБП:\n"
        f"📱 +7 (XXX) XXX-XX-XX\n\n"
        f"После оплаты напиши админу: @{settings.ADMIN_USERNAME}\n\n"
        f"⚠️ В следующей версии будет автоматическая оплата через ЮKassa."
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()