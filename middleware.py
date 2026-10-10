import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

import db
from texts import BUTTON_TO_SECTION

logger = logging.getLogger(__name__)


class StatsMiddleware(BaseMiddleware):
    """Записывает активность пользователя (ID и раздел меню) для статистики. Тексты сообщений не сохраняются."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        try:
            if event.from_user and event.chat.type == "private":
                await db.touch_user(event.from_user.id, BUTTON_TO_SECTION.get(event.text or ""))
        except Exception:  # noqa: BLE001 - статистика не должна ломать бота
            logger.exception("Не удалось записать статистику")
        return await handler(event, data)
