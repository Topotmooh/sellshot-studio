"""Хендлеры стартовых команд бота."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import settings
from bot.webapp_url import get_web_app_url

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start с кнопкой Mini App."""
    user_name = message.from_user.first_name or "Селлер"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Создать карточку в приложении",
                web_app=WebAppInfo(url=get_web_app_url())
            )
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
            InlineKeyboardButton(text="💎 Премиум", callback_data="premium"),
        ],
        [
            InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        ]
    ])

    text = (
        f"Привет, {user_name}! 👋\n\n"
        f"Я создаю студийные карточки для Авито, Юлы, VK Маркет и 7 других площадок с помощью ИИ.\n\n"
        f"✅ Уже создано: 1,240 карточек\n"
        f"⏱️ Сэкономлено времени: 620 часов\n"
        f"✅ Прошли модерацию: 98%\n\n"
        f"🔥 <b>Акция для первых 100 пользователей:</b>\n"
        f"Пакет 10 карточек всего за 490 ₽ (вместо 1500 ₽).\n"
        f"⏳ До конца акции: 2 дня 14 часов.\n\n"
        f"Нажми кнопку ниже, чтобы открыть приложение и загрузить фото!"
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    text = (
        "📖 <b>Как пользоваться SellShot Studio:</b>\n\n"
        f"1️⃣ Нажми кнопку '🚀 Создать карточку в приложении'\n"
        f"2️⃣ Загрузи фото товара (JPG/PNG до 20 МБ)\n"
        f"3️⃣ ИИ обработает фото за 30–60 секунд\n"
        f"4️⃣ Получи готовую карточку + текст описания\n"
        f"5️⃣ Скопируй текст и опубликуй на площадке\n\n"
        f"📱 <b>Поддерживаемые площадки:</b>\n"
        f"• Авито, Юла, VK Маркет\n"
        f"• Яндекс Объявления, gde.ru\n"
        f"• barahla.net, kupipanda.ru\n"
        f"• vkupiprodai.ru, Мешок, Looton\n\n"
        f"💎 <b>Тарифы:</b>\n"
        f"• Бесплатно: 3 карточки в день\n"
        f"• Пакет 10 карточек: 490 ₽ (акция)\n"
        f"• Пакет 100 карточек: 1,990 ₽\n"
        f"• Подписка: 1,490 ₽/мес (безлимит)\n\n"
        f"❓ Вопросы? Пиши админу: @{settings.ADMIN_USERNAME}"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats."""
    text = (
        "📊 <b>Статистика SellShot Studio:</b>\n\n"
        f"✅ Создано карточек: 1,240\n"
        f"⏱️ Сэкономлено времени: 620 часов\n"
        f"✅ Прошли модерацию: 98%\n"
        f"👥 Активных пользователей: 87\n\n"
        f"🔥 Присоединяйся!"
    )

    await message.answer(text, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "stats")
async def callback_stats(callback):
    """Кнопка 'Статистика'."""
    await cmd_stats(callback.message)
    await callback.answer()


@router.callback_query(lambda c: c.data == "premium")
async def callback_premium(callback):
    """Кнопка 'Премиум'."""
    text = (
        "💎 <b>Премиум-тарифы:</b>\n\n"
        f"📦 Пакет 10 карточек: 490 ₽ (акция)\n"
        f"📦 Пакет 100 карточек: 1,990 ₽\n"
        f"🔄 Подписка безлимит: 1,490 ₽/мес\n\n"
        f"Для оплаты переведи сумму на СБП:\n"
        f"📱 +7 (XXX) XXX-XX-XX\n\n"
        f"После оплаты напиши админу: @{settings.ADMIN_USERNAME}\n\n"
        f"⚠️ В следующей версии будет автоматическая оплата через ЮKassa."
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data == "help")
async def callback_help(callback):
    """Кнопка 'Помощь'."""
    await cmd_help(callback.message)
    await callback.answer()