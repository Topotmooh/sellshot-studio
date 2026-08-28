"""Юридический блок: оферта, приватность, согласие, право на забвение."""
from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

from config import logger
from db import database as db

router = Router()

OFFER_TEXT = """📄 <b>Оферта SellShot Studio</b> (кратко)

1. Бот оказывает услугу автоматической обработки фотографий товаров и генерации карточек.
2. Использование бота = акцепт оферты.
3. Бесплатный лимит: 5 карточек в день с водяным знаком. Платные тарифы — по прайсу в боте.
4. Сервис является инструментом обработки контента и <b>не является цифровой платформой</b> по 289-ФЗ: не посредничает в сделках и не получает комиссию с продаж.
5. Ответственность за товар, достоверность характеристик и данные продавца несёт продавец.
6. Возврат средств — в соответствии с законодательством РФ.

Полный текст оферты пришлём после деплоя (ссылка на документ)."""

PRIVACY_TEXT = """🔒 <b>Политика конфиденциальности</b> (кратко)

1. Храним: Telegram ID, учёт лимитов, «паспорт продавца» (если вы его заполнили).
2. Фото товаров удаляются автоматически не позднее 24 часов.
3. Цели обработки: работа сервиса, формирование карточек, учёт лимитов.
4. Данные не передаются третьим лицам, кроме платёжного провайдера при оплате.
5. /consent — дать согласие на обработку данных.
6. /forget — удалить «паспорт продавца» и отозвать согласие (право на забвение, 152-ФЗ)."""


@router.message(Command("offer"))
async def offer_cmd(message: types.Message) -> None:
    await message.answer(OFFER_TEXT)


@router.message(Command("privacy"))
async def privacy_cmd(message: types.Message) -> None:
    await message.answer(PRIVACY_TEXT)


@router.message(Command("consent"))
async def consent_cmd(message: types.Message) -> None:
    await db.set_consent(message.from_user.id)
    await message.answer(
        "✅ Согласие на обработку данных сохранено.\n"
        "Отозвать можно командой /forget."
    )


@router.message(Command("forget"))
async def forget_cmd(message: types.Message) -> None:
    await db.forget_user(message.from_user.id)
    logger.info(" Пользователь %s удалил данные (forget)", message.from_user.id)
    await message.answer(
        "🗑 «Паспорт продавца» удалён, согласие отозвано.\n"
        "Карточки больше не будут содержать блок о продавце."
    )