import html
import logging
import math
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ErrorEvent, LinkPreviewOptions, Message

import content
import data
import db
import keyboards as kb
from auth import DEMO_FIN, DEMO_PASSWORD, FIN_RE, authenticate, get_student
from config import ADMIN_IDS
from store import (
    USER_LANG,
    end_session,
    get_lang,
    get_session,
    lock_remaining,
    register_failure,
    reset_attempts,
    start_session,
)
from texts import LANGS, T, WEEKDAYS, t

logger = logging.getLogger(__name__)

# Азербайджан живёт по UTC+4 без перехода на летнее время
BAKU_TZ = timezone(timedelta(hours=4))
router = Router(name="main")
router.message.filter(F.chat.type == "private")


class Auth(StatesGroup):
    fin = State()
    password = State()


def is_btn(key: str):
    """Фильтр: текст сообщения совпадает с кнопкой `key` на любом из языков."""
    return F.text.in_({T[lang][key] for lang in T})


def _format_items(items: list[dict]) -> str:
    blocks = []
    for item in items:
        date_line = f"📅 {html.escape(item['date'])}\n" if item.get("date") else ""
        link = f"<a href=\"{html.escape(item['url'], quote=True)}\">{html.escape(item['title'])}</a>"
        blocks.append(date_line + link)
    return "\n\n".join(blocks)


# ---------- Старт, язык, меню ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    uid = message.from_user.id
    if uid not in USER_LANG:
        await message.answer(T["az"]["choose_lang"], reply_markup=kb.language_inline())
        return
    lang = get_lang(uid)
    await message.answer(t(lang, "welcome"), reply_markup=kb.main_menu(lang))


@router.message(Command("menu"))
@router.message(is_btn("btn_back"))
async def show_menu(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "menu_title"), reply_markup=kb.main_menu(lang))


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "help"), reply_markup=kb.main_menu(lang))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "cancelled"), reply_markup=kb.main_menu(lang))


@router.message(is_btn("btn_lang"))
async def change_lang(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(T["az"]["choose_lang"], reply_markup=kb.language_inline())


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(call: CallbackQuery, state: FSMContext):
    code = (call.data or "").split(":", 1)[-1]
    if code not in LANGS:
        await call.answer()
        return
    USER_LANG[call.from_user.id] = code
    try:
        await db.set_lang(call.from_user.id, code)
    except Exception:  # noqa: BLE001 - язык остаётся в памяти, бот продолжает работать
        logger.exception("Не удалось сохранить язык пользователя")
    await state.clear()
    await call.answer()
    if isinstance(call.message, Message):
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        await call.message.answer(t(code, "welcome"), reply_markup=kb.main_menu(code))


# ---------- Факультеты ----------

@router.message(is_btn("btn_faculties"))
async def faculties(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "faculties_title"), reply_markup=kb.faculties_inline(lang))


@router.callback_query(F.data.startswith("fac:"))
async def cb_faculty(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    raw = (call.data or "").split(":", 1)[-1]
    if raw == "list":
        text, markup = t(lang, "faculties_title"), kb.faculties_inline(lang)
    else:
        if not raw.isdigit() or int(raw) >= len(data.FACULTIES):
            await call.answer()
            return
        idx = int(raw)
        faculty = data.FACULTIES[idx]
        text = t(
            lang,
            "faculty_card",
            name=html.escape(faculty["name"][lang]),
            dean=html.escape(faculty["dean"]),
            email=faculty["email"],
            phone=faculty["phone"],
        )
        markup = kb.faculty_detail_inline(lang, idx)
    await call.answer()
    if isinstance(call.message, Message):
        try:
            await call.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            pass


# ---------- Поступление, новости, объявления, контакты ----------

@router.message(is_btn("btn_admission"))
async def admission(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "admission"), reply_markup=kb.admission_inline(lang))


@router.message(is_btn("btn_news"))
async def news(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(
        t(lang, "news_title") + "\n" + _format_items(content.get_news()),
        reply_markup=kb.news_inline(lang, "news", await db.is_subscribed(message.from_user.id)),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@router.message(is_btn("btn_ann"))
async def announcements(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(
        t(lang, "ann_title") + "\n" + _format_items(content.get_ann()),
        reply_markup=kb.news_inline(lang, "ann", await db.is_subscribed(message.from_user.id)),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@router.callback_query(F.data.startswith("sub:"))
async def cb_subscribe(call: CallbackQuery):
    uid = call.from_user.id
    lang = get_lang(uid)
    action = (call.data or "").split(":", 1)[-1]
    markup = None
    if action == "off":  # кнопка под самим уведомлением
        await db.set_subscription(uid, False)
        await call.answer(t(lang, "sub_disabled"))
    elif action in ("news", "ann"):
        enabled = not await db.is_subscribed(uid)
        await db.set_subscription(uid, enabled)
        await call.answer(t(lang, "sub_enabled" if enabled else "sub_disabled"))
        markup = kb.news_inline(lang, action, enabled)
    else:
        await call.answer()
        return
    if isinstance(call.message, Message):
        try:
            await call.message.edit_reply_markup(reply_markup=markup)
        except TelegramBadRequest:
            pass


@router.message(is_btn("btn_contacts"))
async def contacts(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    c = content.get_contact()
    await message.answer(
        t(lang, "contacts", address=c["address"], phone=c["phone"], email=c["email"], site=c["site"]),
        reply_markup=kb.contacts_inline(lang),
    )
    await message.answer_location(latitude=c["lat"], longitude=c["lon"])


# ---------- Расписание (файлы, загружаются админом) ----------

@router.message(is_btn("btn_schedule"))
async def schedule(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "schedule_title"), reply_markup=kb.schedule_faculties_inline(lang))


@router.callback_query(F.data.startswith("sch:"))
async def cb_schedule(call: CallbackQuery, bot: Bot):
    lang = get_lang(call.from_user.id)
    parts = (call.data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""
    arg = parts[2] if len(parts) > 2 else ""

    if action == "list":
        await call.answer()
        if isinstance(call.message, Message):
            try:
                await call.message.edit_text(
                    t(lang, "schedule_title"), reply_markup=kb.schedule_faculties_inline(lang)
                )
            except TelegramBadRequest:
                pass
        return

    if action == "f":
        if not arg.isdigit() or int(arg) >= len(data.FACULTIES):
            await call.answer()
            return
        idx = int(arg)
        faculty = html.escape(data.FACULTIES[idx]["name"][lang])
        items = [(sid, label) for sid, _, label in await db.list_schedules(idx)]
        if items:
            text, markup = t(lang, "schedule_pick", faculty=faculty), kb.schedule_list_inline(lang, items)
        else:
            text, markup = t(lang, "schedule_empty", faculty=faculty), kb.schedule_back_inline(lang)
        await call.answer()
        if isinstance(call.message, Message):
            try:
                await call.message.edit_text(text, reply_markup=markup)
            except TelegramBadRequest:
                pass
        return

    if action == "g":
        if not arg.isdigit():
            await call.answer()
            return
        row = await db.get_schedule(int(arg))
        await call.answer()
        if row is None:  # файл удалён админом, пока у пользователя висело старое меню
            await bot.send_message(call.from_user.id, t(lang, "schedule_file_error"))
            return
        file_id, file_type, label, faculty_idx = row
        faculty_name = data.FACULTIES[faculty_idx]["name"][lang] if faculty_idx < len(data.FACULTIES) else ""
        caption = html.escape(f"🗓 {faculty_name} · {label}")
        try:
            if file_type == "photo":
                await bot.send_photo(call.from_user.id, file_id, caption=caption)
            else:
                await bot.send_document(call.from_user.id, file_id, caption=caption)
        except TelegramBadRequest:
            logger.exception("Не удалось отправить расписание id=%s", arg)
            await bot.send_message(call.from_user.id, t(lang, "schedule_file_error"))
        return

    await call.answer()


# ---------- Кабинет студента (демо) ----------

async def show_profile(message: Message, lang: str, fin: str) -> None:
    student = get_student(fin)
    if not student:
        end_session(message.chat.id)
        await message.answer(t(lang, "unknown"), reply_markup=kb.main_menu(lang))
        return
    grades = "\n".join(
        f"• {html.escape(subject[lang])}: <b>{score}</b>" for subject, score in student["grades"]
    )
    text = t(
        lang,
        "profile",
        name=html.escape(student["name"][lang]),
        faculty=html.escape(data.FACULTIES[student["faculty_index"]]["name"][lang]),
        specialty=html.escape(student["specialty"][lang]),
        course=student["course"],
        group=html.escape(student["group"]),
        gpa=student["gpa"],
        grades=grades,
    )
    await message.answer(text, reply_markup=kb.cabinet_menu(lang))


@router.message(is_btn("btn_cabinet"))
async def cabinet(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    session = get_session(uid)
    if session:
        await show_profile(message, lang, session["fin"])
        return
    remaining = lock_remaining(uid)
    if remaining > 0:
        await message.answer(
            t(lang, "locked", minutes=math.ceil(remaining / 60)), reply_markup=kb.main_menu(lang)
        )
        return
    await state.set_state(Auth.fin)
    await message.answer(
        t(lang, "cabinet_intro", fin=DEMO_FIN, password=DEMO_PASSWORD),
        reply_markup=kb.cancel_menu(lang),
    )


def _today_weekday() -> int:
    return datetime.now(BAKU_TZ).weekday()


def _lessons_text(lang: str, lessons: list[dict]) -> str:
    return "\n".join(
        f"🕘 {html.escape(item['time'])} · {html.escape(item['subject'][lang])} · 📍 {html.escape(item['room'])}"
        for item in lessons
    )


def _myschedule_view(lang: str, student: dict, mode: str):
    timetable = student.get("schedule", {})
    if mode == "week":
        blocks = []
        for day in range(5):
            lessons = timetable.get(day, [])
            body = _lessons_text(lang, lessons) if lessons else t(lang, "myschedule_free")
            blocks.append(f"<b>{WEEKDAYS[lang][day]}</b>\n{body}")
        text = t(lang, "myschedule_week", lessons="\n\n".join(blocks))
    else:
        day = _today_weekday()
        lessons = timetable.get(day, [])
        body = _lessons_text(lang, lessons) if lessons else t(lang, "myschedule_none")
        text = t(lang, "myschedule_today", day=WEEKDAYS[lang][day], lessons=body)
    return text, kb.myschedule_inline(lang, "week" if mode == "week" else "today")


@router.message(is_btn("btn_myschedule"))
async def my_schedule(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    session = get_session(uid)
    student = get_student(session["fin"]) if session else None
    if not student:  # нет активной сессии: отправляем на вход в кабинет
        end_session(uid)
        await cabinet(message, state)
        return
    text, markup = _myschedule_view(lang, student, "today")
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.in_({"ms:today", "ms:week"}))
async def cb_myschedule(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    session = get_session(call.from_user.id)
    student = get_student(session["fin"]) if session else None
    if not student:
        await call.answer(t(lang, "session_expired"), show_alert=True)
        return
    text, markup = _myschedule_view(lang, student, "week" if call.data == "ms:week" else "today")
    await call.answer()
    if isinstance(call.message, Message):
        try:
            await call.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            pass


@router.message(is_btn("btn_logout"))
async def logout(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    end_session(uid)
    await message.answer(t(lang, "logged_out"), reply_markup=kb.main_menu(lang))


@router.message(StateFilter(Auth.fin, Auth.password), is_btn("btn_cancel"))
async def cancel_auth(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "cancelled"), reply_markup=kb.main_menu(lang))


@router.message(Auth.fin, F.text)
async def got_fin(message: Message, state: FSMContext):
    if not message.from_user or not message.text:
        return
    lang = get_lang(message.from_user.id)
    fin = message.text.strip().upper()
    if not FIN_RE.fullmatch(fin):
        await message.answer(t(lang, "bad_fin"))
        return
    await state.update_data(fin=fin)
    await state.set_state(Auth.password)
    await message.answer(t(lang, "ask_password"))


@router.message(Auth.password, F.text)
async def got_password(message: Message, state: FSMContext):
    if not message.from_user or not message.text:
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    password = message.text
    try:  # пароль не должен оставаться в истории чата
        await message.delete()
    except TelegramBadRequest:
        pass

    fin = (await state.get_data()).get("fin")
    if not fin:
        await state.clear()
        await message.answer(t(lang, "unknown"), reply_markup=kb.main_menu(lang))
        return

    remaining = lock_remaining(uid)
    if remaining > 0:
        await state.clear()
        await message.answer(
            t(lang, "locked", minutes=math.ceil(remaining / 60)), reply_markup=kb.main_menu(lang)
        )
        return

    student = authenticate(fin, password)
    if student is None:
        left = register_failure(uid)
        if left <= 0:
            await state.clear()
            await message.answer(
                t(lang, "locked", minutes=math.ceil(lock_remaining(uid) / 60)),
                reply_markup=kb.main_menu(lang),
            )
        else:
            await state.set_state(Auth.fin)
            await message.answer(t(lang, "wrong_creds", left=left), reply_markup=kb.cancel_menu(lang))
        return

    reset_attempts(uid)
    start_session(uid, fin)
    await state.clear()
    await show_profile(message, lang, fin)


@router.message(StateFilter(Auth.fin, Auth.password))
async def auth_non_text(message: Message):
    if not message.from_user:
        return
    await message.answer(t(get_lang(message.from_user.id), "only_text"))


# ---------- Прочее ----------

@router.message()
async def fallback(message: Message):
    if not message.from_user:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "unknown"), reply_markup=kb.main_menu(lang))


@router.error()
async def on_error(event: ErrorEvent, bot: Bot):
    logger.exception("Unhandled error", exc_info=event.exception)
    text = f"⚠️ Bot error: <code>{html.escape(repr(event.exception))[:500]}</code>"
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:  # noqa: BLE001 - уведомление не должно ломать бота
            logger.warning("Could not notify admin %s", admin_id)
    return True
