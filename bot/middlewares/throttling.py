"""Флуд-защита: не чаще 1 сообщения в 0.7 сек с одного пользователя."""
from __future__ import annotations

import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

MIN_INTERVAL = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._last: dict[int, float] = {}

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = getattr(event, "from_user", None)
        if user is not None:
            if len(self._last) > 20000:
                self._last.clear()

            now = time.monotonic()
            last = self._last.get(user.id, 0.0)
            if now - last < MIN_INTERVAL:
                return  # молча игнорируем
            self._last[user.id] = now

        return await handler(event, data)