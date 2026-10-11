"""Рассылка подписчикам уведомлений о новых новостях и объявлениях с сайта."""
import asyncio
import html
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import LinkPreviewOptions

import db
import keyboards as kb
from store import get_lang
from texts import t

logger = logging.getLogger(__name__)


def build_text(lang: str, items: list[dict]) -> str:
    blocks = []
    for item in items:
        header = t(lang, "alert_news" if item.get("kind") == "news" else "alert_ann")
        date_line = f"\n📅 {html.escape(item['date'])}" if item.get("date") else ""
        link = f"<a href=\"{html.escape(item['url'], quote=True)}\">{html.escape(item['title'])}</a>"
        blocks.append(f"{header}{date_line}\n{link}")
    return "\n\n".join(blocks)


async def _send(bot: Bot, uid: int, text: str, lang: str) -> str:
    """Возвращает 'sent', 'blocked' или 'failed'."""
    kwargs = {
        "reply_markup": kb.alert_inline(lang),
        "link_preview_options": LinkPreviewOptions(is_disabled=True),
    }
    try:
        await bot.send_message(uid, text, **kwargs)
        return "sent"
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        try:
            await bot.send_message(uid, text, **kwargs)
            return "sent"
        except Exception:  # noqa: BLE001
            return "failed"
    except TelegramForbiddenError:
        await db.mark_blocked(uid)
        return "blocked"
    except Exception:  # noqa: BLE001
        logger.exception("Не удалось отправить уведомление пользователю %s", uid)
        return "failed"


async def notify_new_items(bot: Bot, items: list[dict]) -> None:
    """Отправляет подписчикам одно сообщение со всеми новыми материалами (от старых к новым)."""
    if not items:
        return
    ordered = list(reversed(items))  # на сайте новые идут первыми
    stats = {"sent": 0, "blocked": 0, "failed": 0}
    for uid in await db.subscriber_ids():
        lang = get_lang(uid)
        result = await _send(bot, uid, build_text(lang, ordered), lang)
        stats[result] += 1
        await asyncio.sleep(0.05)  # ~20 сообщений/с, ниже лимита Telegram
    logger.info("Уведомления о новостях: %s", stats)
