"""Админ-панель внутри бота (/admin). Доступна только пользователям из ADMIN_IDS (.env).

Возможности: статистика, рассылка всем пользователям, обновление новостей вручную, правка контактов.
Язык панели совпадает с языком, выбранным администратором в боте (az / ru / en); тексты в admin_texts.py.
"""
import asyncio
import html
import logging
import re
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import content
import db
from admin_texts import at, section_name
from config import ADMIN_IDS
from store import get_lang
from texts import ALL_REPLY_BUTTONS

logger = logging.getLogger(__name__)

admin_router = Router(name="admin")
admin_router.message.filter(F.chat.type == "private", F.from_user.id.in_(ADMIN_IDS))
admin_router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))

FIELDS = ("phone", "email", "address")
MAX_BROADCAST_LEN = 3500

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[0-9+()\-\s]{5,30}$")
_tasks: set[asyncio.Task] = set()

# Обычный текст пользователя (не команда и не кнопка меню)
_PLAIN_TEXT = (F.text, ~F.text.startswith("/"), ~F.text.in_(ALL_REPLY_BUTTONS))


class Broadcast(StatesGroup):
    text = State()
    confirm = State()


class EditContact(StatesGroup):
    value = State()


def _kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows]
    )


def panel_kb(lang: str) -> InlineKeyboardMarkup:
    return _kb(
        [
            [(at(lang, "btn_stats"), "adm:stats")],
            [(at(lang, "btn_broadcast"), "adm:bc")],
            [(at(lang, "btn_refresh"), "adm:news")],
            [(at(lang, "btn_contacts"), "adm:contacts")],
        ]
    )


def back_kb(lang: str) -> InlineKeyboardMarkup:
    return _kb([[(at(lang, "btn_home"), "adm:home")]])


async def _edit(call: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    if isinstance(call.message, Message):
        try:
            await call.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            pass


# ---------- Вход и главная ----------

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    await message.answer(at(lang, "panel"), reply_markup=panel_kb(lang))


@admin_router.callback_query(F.data == "adm:home")
async def cb_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    lang = get_lang(call.from_user.id)
    await _edit(call, at(lang, "panel"), panel_kb(lang))


# ---------- Статистика ----------

@admin_router.callback_query(F.data == "adm:stats")
async def cb_stats(call: CallbackQuery):
    await call.answer()
    lang = get_lang(call.from_user.id)
    s = await db.get_stats()
    langs = " · ".join(f"{code} {cnt}" for code, cnt in sorted(s["langs"].items())) or "—"
    top = "\n".join(
        f"• {section_name(lang, section)}: {cnt}" for section, cnt in s["top_sections"]
    ) or at(lang, "no_data")
    updated = content.last_update()
    updated_text = (
        time.strftime("%d.%m.%Y %H:%M", time.localtime(updated)) if updated else at(lang, "never_updated")
    )
    text = at(
        lang,
        "stats",
        total=s["total"],
        a24=s["active_24h"],
        a7=s["active_7d"],
        blocked=s["blocked"],
        langs=html.escape(langs),
        top=top,
        updated=updated_text,
    )
    await _edit(call, text, back_kb(lang))


# ---------- Обновление новостей ----------

@admin_router.callback_query(F.data == "adm:news")
async def cb_news(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    await call.answer(at(lang, "refreshing"))
    result = await content.refresh()
    if result["ok"]:
        titles = "\n".join(f"• {html.escape(i['title'])[:80]}" for i in content.get_news()[:3])
        text = at(lang, "news_ok", news=result["news"], ann=result["ann"], titles=titles)
    else:
        text = at(lang, "news_fail", error=html.escape(str(result["error"]))[:500])
    await _edit(call, text, back_kb(lang))


# ---------- Рассылка ----------

@admin_router.callback_query(F.data == "adm:bc")
async def cb_bc(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    await state.set_state(Broadcast.text)
    await call.answer()
    await _edit(
        call,
        at(lang, "bc_prompt", max=MAX_BROADCAST_LEN),
        _kb([[(at(lang, "btn_cancel"), "adm:home")]]),
    )


@admin_router.message(Broadcast.text, *_PLAIN_TEXT)
async def got_broadcast_text(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    text = (message.text or "").strip()
    if not text or len(text) > MAX_BROADCAST_LEN:
        await message.answer(at(lang, "bc_bad_length", max=MAX_BROADCAST_LEN))
        return
    await state.update_data(text=text)
    await state.set_state(Broadcast.confirm)
    count = len(await db.recipient_ids())
    await message.answer(
        at(lang, "bc_preview", count=count, text=text),
        parse_mode=None,
        reply_markup=_kb([[(at(lang, "btn_send_all"), "adm:bc_send"), (at(lang, "btn_cancel"), "adm:home")]]),
    )


@admin_router.callback_query(F.data == "adm:bc_send", StateFilter(Broadcast.confirm))
async def cb_bc_send(call: CallbackQuery, state: FSMContext, bot: Bot):
    lang = get_lang(call.from_user.id)
    text = (await state.get_data()).get("text")
    await state.clear()
    await call.answer()
    if not text:
        return
    await _edit(call, at(lang, "bc_started"), None)
    task = asyncio.create_task(_broadcast(bot, call.from_user.id, text))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def _broadcast(bot: Bot, admin_id: int, text: str) -> None:
    sent = blocked = failed = 0
    for uid in await db.recipient_ids():
        try:
            await bot.send_message(uid, text, parse_mode=None)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.send_message(uid, text, parse_mode=None)
                sent += 1
            except Exception:  # noqa: BLE001
                failed += 1
        except TelegramForbiddenError:
            blocked += 1
            await db.mark_blocked(uid)
        except Exception:  # noqa: BLE001
            logger.exception("Не удалось отправить рассылку пользователю %s", uid)
            failed += 1
        await asyncio.sleep(0.05)  # ~20 сообщений/с, ниже лимита Telegram
    try:
        await bot.send_message(
            admin_id, at(get_lang(admin_id), "bc_report", sent=sent, blocked=blocked, failed=failed)
        )
    except Exception:  # noqa: BLE001
        logger.warning("Не удалось отправить отчёт о рассылке администратору %s", admin_id)


# ---------- Контакты ----------

def _contacts_view(lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = content.get_contact()
    text = at(
        lang,
        "contacts_view",
        address=html.escape(c["address"]),
        phone=html.escape(c["phone"]),
        email=html.escape(c["email"]),
    )
    markup = _kb(
        [
            [(at(lang, "btn_phone"), "adm:ce:phone"), (at(lang, "btn_email"), "adm:ce:email")],
            [(at(lang, "btn_address"), "adm:ce:address")],
            [(at(lang, "btn_reset"), "adm:cereset")],
            [(at(lang, "btn_home"), "adm:home")],
        ]
    )
    return text, markup


@admin_router.callback_query(F.data == "adm:contacts")
async def cb_contacts(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    text, markup = _contacts_view(get_lang(call.from_user.id))
    await _edit(call, text, markup)


@admin_router.callback_query(F.data.startswith("adm:ce:"))
async def cb_edit_contact(call: CallbackQuery, state: FSMContext):
    field = (call.data or "").split(":")[-1]
    if field not in FIELDS:
        await call.answer()
        return
    lang = get_lang(call.from_user.id)
    await state.set_state(EditContact.value)
    await state.update_data(field=field)
    await call.answer()
    await _edit(
        call,
        at(lang, "ce_prompt", field=at(lang, f"f_{field}")),
        _kb([[(at(lang, "btn_cancel"), "adm:contacts")]]),
    )


@admin_router.callback_query(F.data == "adm:cereset")
async def cb_reset_contacts(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    await content.reset_contacts()
    await call.answer(at(lang, "reset_done"))
    text, markup = _contacts_view(lang)
    await _edit(call, text, markup)


def _validate(field: str, value: str) -> str | None:
    """Возвращает ключ текста ошибки или None, если значение корректно."""
    if field == "phone" and not _PHONE_RE.match(value):
        return "err_phone"
    if field == "email" and (len(value) > 100 or not _EMAIL_RE.match(value)):
        return "err_email"
    if field == "address" and not (5 <= len(value) <= 200):
        return "err_address"
    return None


@admin_router.message(EditContact.value, *_PLAIN_TEXT)
async def got_contact_value(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    field = (await state.get_data()).get("field")
    value = (message.text or "").strip()
    if field not in FIELDS:
        await state.clear()
        return
    error_key = _validate(field, value)
    if error_key:
        await message.answer(f"❗️ {at(lang, error_key)}\n{at(lang, 'retry')}")
        return
    await content.set_contact(field, value)
    await state.clear()
    text, markup = _contacts_view(lang)
    await message.answer(at(lang, "saved") + "\n\n" + text, reply_markup=markup)


# ---------- Устаревшие кнопки ----------

@admin_router.callback_query(F.data.startswith("adm:"))
async def cb_stale(call: CallbackQuery):
    await call.answer(at(get_lang(call.from_user.id), "stale"), show_alert=False)
