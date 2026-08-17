"""Обработчик /start."""
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards.menus import profile_keyboard
from config import settings
from db import database as db

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()

    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    await message.answer(
        f"Привет! Это {settings.APP_NAME}.\n\n"
        "Я делаю продающие карточки товара по фото.\n\n"
        "Шаг 1 из 3 — выбери тип карточки:",
        reply_markup=profile_keyboard(),
    )