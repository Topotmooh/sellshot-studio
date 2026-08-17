"""Инлайн-клавиатуры бота."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings
from core.profiles import PROFILES

CATEGORIES = [
    ("clothes", "👕 Одежда"),
    ("shoes", "👟 Обувь"),
    ("electronics", "📱 Электроника"),
    ("bags", "👜 Сумки"),
    ("furniture", "🛋 Мебель"),
    ("other", "📦 Другое"),
]


def profile_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key in settings.enabled_profiles_list:
        profile = PROFILES.get(key)
        if profile is not None:
            rows.append([
                InlineKeyboardButton(
                    text=profile.display_name,
                    callback_data=f"profile:{key}",
                )
            ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"category:{key}")]
        for key, name in CATEGORIES
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)