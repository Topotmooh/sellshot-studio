"""Приём фото, валидация и сборка карточки + комплаенс-блок 289-ФЗ."""
from __future__ import annotations

import asyncio
import html
import re

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from ai.base_provider import generate_background
from config import logger, settings
from core.profiles import get_profile
from core.states import CardStates
from db import database as db
from services import compositor, limits, segmenter, storage, validator, watermark

router = Router()

# Защита от поддельных callback_data: только безопасные символы
_SAFE_VALUE = re.compile(r"[a-z0-9_]{1,32}")

# Лок «одна обработка на пользователя»: не даём заспамить CPU-очередь
_processing_users: set[int] = set()


def _safe_profile(raw: object) -> str:
    if isinstance(raw, str) and _SAFE_VALUE.fullmatch(raw):
        return raw
    return settings.DEFAULT_PROFILE


def _safe_category(raw: object) -> str:
    if isinstance(raw, str) and _SAFE_VALUE.fullmatch(raw):
        return raw
    return "other"


@router.message(CardStates.waiting_photo, F.photo)
async def photo_received(message: types.Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    profile = get_profile(_safe_profile(data.get("profile")))
    category = _safe_category(data.get("category"))

    # 0. Проверка лимита
    allowed, used, limit = await limits.check_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            f"⛔ Дневной лимит исчерпан: {limit} фото.\n\n"
            "Лимит сбрасывается каждый день в 00:00 (UTC).\n"
            "Платные тарифы без лимита — скоро."
        )
        return

    # 0.5. Лок: не больше одной одновременной обработки на пользователя
    user_id = message.from_user.id
    if user_id in _processing_users:
        await message.answer("⏳ Уже обрабатываю предыдущее фото — подожди немного.")
        return
    _processing_users.add(user_id)

    try:
        photo = message.photo[-1]

        # 1. Проверка размера до скачивания
        try:
            validator.check_size_before_download(photo.file_size)
        except validator.ValidationError as e:
            await message.answer(f"⚠️ {e}")
            return

        # 2. Сохраняем под случайным именем
        saved_path = storage.new_temp_path(suffix=".jpg")

        try:
            await bot.download(photo, destination=str(saved_path))
        except Exception:
            logger.exception("Не удалось скачать фото")
            storage.safe_unlink(saved_path)
            await message.answer("❌ Не удалось скачать фото. Попробуй ещё раз.")
            return

        # 3. Проверка реального файла
        try:
            validator.check_file_after_download(saved_path)
        except validator.ValidationError as e:
            storage.safe_unlink(saved_path)
            await message.answer(f"⚠️ {e}")
            return

        # 4. Используем оригинальное фото
        processing_path = saved_path

        await state.update_data(photo_path=str(processing_path))

        # 5. Вырезание товара
        status = await message.answer("⏳ Вырезаю товар с фона...")

        cutout_path = storage.new_temp_path(suffix=".png")

        try:
            await segmenter.cutout_product(processing_path, cutout_path)
        except (asyncio.TimeoutError, TimeoutError):
            storage.safe_unlink(cutout_path)
            await status.edit_text(
                "⏰ Обработка заняла слишком много времени. Попробуй фото попроще."
            )
            return
        except Exception:
            logger.exception("Ошибка вырезания товара")
            storage.safe_unlink(cutout_path)
            await status.edit_text("❌ Не удалось вырезать товар. Попробуй другое фото.")
            return

        await state.update_data(cutout_path=str(cutout_path))

        # 6. AI-фон (если подключён), иначе локальный
        background_path = None
        if settings.AI_PROVIDER in ("yandex", "sber"):
            await status.edit_text("🎨 Генерирую AI-фон...")
            background_path = await generate_background(
                profile.output_width,
                profile.output_height,
                category,
                profile.ai_style,
            )
            if background_path is None:
                await status.edit_text("🎨 AI-фон недоступен, использую студийный фон.")

        # 7. Сборка карточки
        await status.edit_text("🧩 Собираю карточку: тень, размер, формат...")

        result_path = storage.new_result_path(suffix=".jpg")

        try:
            await compositor.compose_card(
                cutout_path,
                result_path,
                profile,
                category,
                background_path,
            )
        except Exception:
            logger.exception("Ошибка сборки карточки")
            storage.safe_unlink(result_path)
            await status.edit_text("❌ Не удалось собрать карточку. Попробуй другое фото.")
            return
        finally:
            if background_path is not None:
                storage.safe_unlink(background_path)

        # 8. Водяной знак для бесплатных
        if settings.ENABLE_WATERMARK and not await limits.is_premium_user(user_id):
            watermark.watermark_file(result_path, settings.WATERMARK_TEXT)

        # 9. Учёт использования
        await limits.consume(
            user_id,
            profile.key,
            category,
            settings.AI_PROVIDER != "local",
        )

        await state.update_data(result_path=str(result_path))
        await status.edit_text("✅ Карточка готова! Отправляю.")

        # 10. Комплаенс-блок 289-ФЗ (если заполнен паспорт продавца)
        passport = await db.get_passport(user_id)
        compliance = ""
        if passport:
            compliance = (
                "\n\n👤 Продавец: " + html.escape(passport["name"]) +
                "\n📎 Статус: " + html.escape(passport["status"]) +
                " · Город: " + html.escape(passport["city"]) +
                "\nℹ️ Информация о продавце указана в соответствии с 289-ФЗ (с 01.10.2026)."
            )

        await message.answer_photo(
            FSInputFile(str(result_path), filename="card.jpg"),
            caption=(
                "🛍 Готовая карточка.\n\n"
                f"Профиль: {profile.display_name}\n"
                f"Категория: {category}\n"
                f"Использовано сегодня: {used + 1} из {limit if limit else '∞'}"
                + compliance +
                "\n\nБез водяного знака и без лимита — в платных тарифах (скоро)."
            ),
        )
    finally:
        # Лок снимается ЛЮБЫМ выходом из обработки
        _processing_users.discard(user_id)


@router.message(F.document)
async def document_hint(message: types.Message) -> None:
    await message.answer(
        "📄 Ты отправил файл документом.\n\n"
        "Отправь фото как изображение (не как файл), "
        "чтобы я получил его в хорошем качестве."
    )


@router.message(F.photo)
async def photo_without_flow(message: types.Message) -> None:
    await message.answer("Сначала выбери тип карточки — нажми /start")