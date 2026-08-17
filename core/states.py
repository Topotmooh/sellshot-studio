"""FSM-состояния сценария создания карточки."""
from aiogram.fsm.state import State, StatesGroup


class CardStates(StatesGroup):
    waiting_category = State()
    waiting_photo = State()