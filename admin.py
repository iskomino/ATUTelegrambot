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
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Message

import content
import data
import db
import keyboards as kb
import notifier
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
MAX_LABEL_LEN = 40
MAX_FILE_MB = 20

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


class ScheduleAdd(StatesGroup):
    label = State()
    file = State()


async def _is_stray_input(message: Message) -> bool:
    """Любое сообщение, кроме команд и кнопок меню (в том числе стикеры, голосовые и т.п.)."""
    text = message.text
    return not (text and (text.startswith("/") or text in ALL_REPLY_BUTTONS))


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
            [(at(lang, "btn_alert_preview"), "adm:alert")],
            [(at(lang, "btn_schedule"), "adm:sch")],
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
        subs=s["subscribers"],
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


# ---------- Пример уведомления (только администратору) ----------

@admin_router.callback_query(F.data == "adm:alert")
async def cb_alert_preview(call: CallbackQuery, bot: Bot):
    """Присылает ТОЛЬКО администратору пример уведомления с последней новостью (для демонстрации)."""
    lang = get_lang(call.from_user.id)
    await call.answer(at(lang, "alert_preview_sent"))
    news = content.get_news()
    if not news:
        return
    await bot.send_message(
        call.from_user.id,
        notifier.build_text(lang, [dict(news[0], kind="news")]),
        reply_markup=kb.alert_inline(lang),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


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


# ---------- Расписание (файлы) ----------

async def _schedule_view(lang: str) -> tuple[str, InlineKeyboardMarkup]:
    by_faculty: dict[int, list[str]] = {}
    for _, faculty_idx, label in await db.list_schedules():
        by_faculty.setdefault(faculty_idx, []).append(label)
    lines = []
    for i, faculty in enumerate(data.FACULTIES):
        labels = by_faculty.get(i)
        value = html.escape(", ".join(labels)) if labels else at(lang, "sch_none_faculty")
        lines.append(f"🏛 <b>{html.escape(faculty['name'][lang])}</b>: {value}")
    markup = _kb(
        [
            [(at(lang, "btn_sch_add"), "adm:sch_add")],
            [(at(lang, "btn_sch_del"), "adm:sch_delmenu")],
            [(at(lang, "btn_home"), "adm:home")],
        ]
    )
    return at(lang, "sch_title", summary="\n".join(lines)), markup


@admin_router.callback_query(F.data == "adm:sch")
async def cb_sch(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    text, markup = await _schedule_view(get_lang(call.from_user.id))
    await _edit(call, text, markup)


@admin_router.callback_query(F.data == "adm:sch_add")
async def cb_sch_add(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    lang = get_lang(call.from_user.id)
    rows = [[(f["name"][lang], f"adm:sch_f:{i}")] for i, f in enumerate(data.FACULTIES)]
    rows.append([(at(lang, "btn_cancel"), "adm:sch")])
    await _edit(call, at(lang, "sch_pick_faculty"), _kb(rows))


@admin_router.callback_query(F.data.startswith("adm:sch_f:"))
async def cb_sch_faculty(call: CallbackQuery, state: FSMContext):
    raw = (call.data or "").split(":")[-1]
    if not raw.isdigit() or int(raw) >= len(data.FACULTIES):
        await call.answer()
        return
    lang = get_lang(call.from_user.id)
    idx = int(raw)
    await state.set_state(ScheduleAdd.label)
    await state.update_data(faculty=idx)
    await call.answer()
    await _edit(
        call,
        at(lang, "sch_ask_label", faculty=html.escape(data.FACULTIES[idx]["name"][lang]), max=MAX_LABEL_LEN),
        _kb([[(at(lang, "btn_cancel"), "adm:sch")]]),
    )


@admin_router.message(ScheduleAdd.label, *_PLAIN_TEXT)
async def got_sch_label(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    label = (message.text or "").strip()
    if not 1 <= len(label) <= MAX_LABEL_LEN:
        await message.answer(at(lang, "sch_bad_label", max=MAX_LABEL_LEN))
        return
    await state.update_data(label=label)
    await state.set_state(ScheduleAdd.file)
    await message.answer(at(lang, "sch_ask_file"), reply_markup=_kb([[(at(lang, "btn_cancel"), "adm:sch")]]))


@admin_router.message(ScheduleAdd.file, F.document | F.photo)
async def got_sch_file(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    stored = await state.get_data()
    faculty_idx, label = stored.get("faculty"), stored.get("label")
    if not isinstance(faculty_idx, int) or not 0 <= faculty_idx < len(data.FACULTIES) or not label:
        await state.clear()
        return
    if message.document:
        if (message.document.file_size or 0) > MAX_FILE_MB * 1024 * 1024:
            await message.answer(at(lang, "sch_file_too_big", max=MAX_FILE_MB))
            return
        file_id, file_type = message.document.file_id, "document"
    else:
        file_id, file_type = message.photo[-1].file_id, "photo"
    await db.add_schedule(faculty_idx, label, file_id, file_type)
    await state.clear()
    text, markup = await _schedule_view(lang)
    await message.answer(at(lang, "sch_saved") + "\n\n" + text, reply_markup=markup)


@admin_router.message(ScheduleAdd.file, _is_stray_input)
async def sch_file_wrong(message: Message):
    await message.answer(at(get_lang(message.from_user.id), "sch_bad_file"))


async def _delete_menu(lang: str) -> tuple[str, InlineKeyboardMarkup]:
    rows_db = await db.list_schedules()
    if not rows_db:
        return at(lang, "sch_del_empty"), _kb([[(at(lang, "btn_home"), "adm:sch")]])
    rows = []
    for sid, faculty_idx, label in rows_db:
        faculty = data.FACULTIES[faculty_idx]["name"][lang] if faculty_idx < len(data.FACULTIES) else "?"
        rows.append([(f"🗑 {faculty[:22]}: {label}"[:60], f"adm:sch_del:{sid}")])
    rows.append([(at(lang, "btn_home"), "adm:sch")])
    return at(lang, "sch_del_title"), _kb(rows)


@admin_router.callback_query(F.data == "adm:sch_delmenu")
async def cb_sch_delmenu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    text, markup = await _delete_menu(get_lang(call.from_user.id))
    await _edit(call, text, markup)


@admin_router.callback_query(F.data.startswith("adm:sch_del:"))
async def cb_sch_delete(call: CallbackQuery):
    raw = (call.data or "").split(":")[-1]
    lang = get_lang(call.from_user.id)
    if not raw.isdigit():
        await call.answer()
        return
    await db.delete_schedule(int(raw))
    await call.answer(at(lang, "sch_deleted"))
    text, markup = await _delete_menu(lang)
    await _edit(call, text, markup)


# ---------- Устаревшие кнопки ----------

@admin_router.callback_query(F.data.startswith("adm:"))
async def cb_stale(call: CallbackQuery):
    await call.answer(at(get_lang(call.from_user.id), "stale"), show_alert=False)
