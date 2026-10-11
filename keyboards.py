from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

import data
from texts import LANGS, t


def _reply(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text) for text in row] for row in rows],
        resize_keyboard=True,
    )


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return _reply(
        [
            [t(lang, "btn_faculties"), t(lang, "btn_admission")],
            [t(lang, "btn_news"), t(lang, "btn_ann")],
            [t(lang, "btn_schedule"), t(lang, "btn_contacts")],
            [t(lang, "btn_cabinet"), t(lang, "btn_lang")],
        ]
    )


def cancel_menu(lang: str) -> ReplyKeyboardMarkup:
    return _reply([[t(lang, "btn_cancel")]])


def cabinet_menu(lang: str) -> ReplyKeyboardMarkup:
    return _reply([[t(lang, "btn_myschedule")], [t(lang, "btn_logout")], [t(lang, "btn_back")]])


def language_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"lang:{code}")]
            for code, label in LANGS.items()
        ]
    )


def faculties_inline(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f["name"][lang], callback_data=f"fac:{i}")]
            for i, f in enumerate(data.FACULTIES)
        ]
    )


def faculty_detail_inline(lang: str, idx: int) -> InlineKeyboardMarkup:
    faculty = data.FACULTIES[idx]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_site"), url=f"{data.SITE}/fakulte/{faculty['slug']}")],
            [InlineKeyboardButton(text=t(lang, "btn_back_inline"), callback_data="fac:list")],
        ]
    )


def admission_inline(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, key), url=url)] for key, url in data.LINKS.items()
        ]
    )


def single_link(text: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, url=url)]])


def contacts_inline(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_site"), url=data.SITE)],
            [InlineKeyboardButton(text=t(lang, "btn_lms"), url=data.LMS_URL)],
        ]
    )


def schedule_faculties_inline(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f["name"][lang], callback_data=f"sch:f:{i}")]
            for i, f in enumerate(data.FACULTIES)
        ]
    )


def schedule_list_inline(lang: str, items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"📄 {label}"[:60], callback_data=f"sch:g:{sid}")] for sid, label in items]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back_inline"), callback_data="sch:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_back_inline(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_back_inline"), callback_data="sch:list")]]
    )


def myschedule_inline(lang: str, mode: str) -> InlineKeyboardMarkup:
    if mode == "today":
        button = InlineKeyboardButton(text=t(lang, "btn_week"), callback_data="ms:week")
    else:
        button = InlineKeyboardButton(text=t(lang, "btn_today"), callback_data="ms:today")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])

