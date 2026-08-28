"""Паспорт продавца: комплаенс-блок для карточек (289-ФЗ с 01.10.2026)."""
from __future__ import annotations

import html

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import database as db

router = Router()

STATUS_MAP = {
    "self_emp": "Самозанятый (НПД)",
    "ip": "ИП",
    "ooo": "ООО",
    "phys": "Физлицо",
}


class PassportStates(StatesGroup):
    waiting_name = State()
    waiting_status = State()
    waiting_city = State()


def _status_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, title in STATUS_MAP.items():
        builder.button(text=title, callback_data=f"pstat:{code}")
    builder.adjust(2)
    return builder.as_markup()


@router.message(Command("passport"))
async def passport_start(message: types.Message, state: FSMContext) -> None:
    await state.set_state(PassportStates.waiting_name)
    await message.answer(
        "📋 <b>Паспорт продавца</b> (для карточек по 289-ФЗ)\n\n"
        "С 01.10.2026 площадки требуют указывать данные продавца.\n"
        "Заполни один раз — и бот будет автоматически добавлять\n"
        "блок о продавце к описанию каждой карточки.\n\n"
        "<b>1/3.</b> Как вас зовут (имя или название)?"
    )


@router.message(PassportStates.waiting_name)
async def passport_name(message: types.Message, state: FSMContext) -> None:
    name = (message.text or "").strip()[:64]
    if len(name) < 2:
        await message.answer("⚠️ Слишком короткое имя. Попробуй ещё раз.")
        return

    await state.update_data(name=name)
    await state.set_state(PassportStates.waiting_status)
    await message.answer("<b>2/3.</b> Твой статус:", reply_markup=_status_keyboard())


@router.callback_query(PassportStates.waiting_status, F.data.startswith("pstat:"))
async def passport_status(callback: types.CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    if code not in STATUS_MAP:
        await callback.answer("⚠️ Неизвестный статус", show_alert=True)
        return

    await state.update_data(status=STATUS_MAP[code])
    await state.set_state(PassportStates.waiting_city)
    await callback.answer()
    await callback.message.edit_text(
        f"✅ Статус: <b>{html.escape(STATUS_MAP[code])}</b>\n\n<b>3/3.</b> Укажи город:"
    )


@router.message(PassportStates.waiting_city)
async def passport_city(message: types.Message, state: FSMContext) -> None:
    city = (message.text or "").strip()[:40]
    if len(city) < 2:
        await message.answer("⚠️ Слишком короткий город. Попробуй ещё раз.")
        return

    data = await state.get_data()
    await db.save_passport(message.from_user.id, data["name"], data["status"], city)
    await db.set_consent(message.from_user.id)
    await state.clear()

    # ЭКРАНИРОВАНИЕ пользовательского ввода (parse_mode=HTML)
    name_safe = html.escape(data["name"])
    status_safe = html.escape(data["status"])
    city_safe = html.escape(city)

    await message.answer(
        "✅ <b>Паспорт продавца сохранён.</b>\n\n"
        f"👤 {name_safe}\n📎 {status_safe} · {city_safe}\n\n"
        "Теперь к каждой карточке будет добавляться блок о продавце —\n"
        "это повышает доверие покупателей и соответствует 289-ФЗ.\n"
        "Изменить: /passport · Удалить: /forget"
    )