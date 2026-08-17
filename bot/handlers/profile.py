"""Выбор профиля карточки."""
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from bot.keyboards.menus import category_keyboard
from core.profiles import get_profile
from core.states import CardStates

router = Router()


@router.callback_query(F.data.startswith("profile:"))
async def profile_selected(callback: types.CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    profile = get_profile(key)

    await state.set_state(CardStates.waiting_category)
    await state.update_data(profile=key)

    await callback.message.edit_text(
        f"✅ Профиль: {profile.display_name}\n\n"
        "Шаг 2 из 3 — выбери категорию товара:",
        reply_markup=category_keyboard(),
    )
    await callback.answer()