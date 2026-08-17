"""Проверка загружаемых фото."""
from __future__ import annotations

from pathlib import Path

import filetype

from config import settings

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


class ValidationError(Exception):
    """Ошибка валидации файла."""


def check_size_before_download(file_size: int | None) -> None:
    """Быстрая проверка по данным Telegram до скачивания."""
    if file_size is None:
        return

    limit = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024
    if file_size > limit:
        raise ValidationError(
            f"Файл слишком большой. Лимит: {settings.MAX_PHOTO_SIZE_MB} МБ."
        )


def check_file_after_download(path: Path) -> None:
    """Проверка реального файла после сохранения."""
    if not path.exists():
        raise ValidationError("Не удалось сохранить файл.")

    size = path.stat().st_size
    limit = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024

    if size > limit:
        raise ValidationError(
            f"Файл слишком большой. Лимит: {settings.MAX_PHOTO_SIZE_MB} МБ."
        )

    if size < 1024:
        raise ValidationError("Файл слишком маленький, чтобы быть фото.")

    kind = filetype.guess(path)
    if kind is None or kind.mime not in ALLOWED_MIME:
        raise ValidationError("Поддерживаются только JPG, PNG и WebP.")