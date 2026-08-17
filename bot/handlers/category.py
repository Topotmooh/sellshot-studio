"""Выбор категории товара."""
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from core.states import CardStates

router = Router()


@router.callback_query(F.data.startswith("category:"))
async def category_selected(callback: types.CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]

    await state.set_state(CardStates.waiting_photo)
    await state.update_data(category=key)

    await callback.message.edit_text(
        "✅ Категория принята.\n\n"
        "Шаг 3 из 3 — отправь фото товара.\n\n"
        "Совет: снимай при хорошем свете, товар крупным планом."
    )
    await callback.answer()