"""Актуальный контент бота: новости/объявления (автообновление с сайта) и контакты (правятся админом).

Если сайт недоступен или вёрстка изменилась, остаются последние сохранённые данные —
бот никогда не показывает пустой раздел.
"""
import asyncio
import json
import logging
import time

import aiohttp

import data
import db
from site_parser import BASE_URL, parse_home

logger = logging.getLogger(__name__)

MAX_ITEMS = 5
CONTACT_FIELDS = ("phone", "email", "address")

_state: dict = {"news": list(data.NEWS), "ann": list(data.ANNOUNCEMENTS), "updated": None}
_contact_overrides: dict[str, str] = {}
_refresh_lock = asyncio.Lock()


def _valid_items(items) -> bool:
    return (
        isinstance(items, list)
        and all(isinstance(i, dict) and i.get("title") and i.get("url") for i in items)
    )


async def load() -> None:
    """Подтягивает сохранённые данные из БД при старте."""
    raw = await db.kv_get("news_cache")
    if raw:
        try:
            cached = json.loads(raw)
            if _valid_items(cached.get("news")) and cached["news"]:
                _state["news"] = cached["news"]
            if _valid_items(cached.get("ann")) and cached["ann"]:
                _state["ann"] = cached["ann"]
            _state["updated"] = cached.get("updated")
        except (ValueError, AttributeError):
            logger.warning("Кэш новостей повреждён, используются данные по умолчанию")
    raw = await db.kv_get("contact_overrides")
    if raw:
        try:
            stored = json.loads(raw)
            _contact_overrides.update({k: v for k, v in stored.items() if k in CONTACT_FIELDS and isinstance(v, str)})
        except (ValueError, AttributeError):
            logger.warning("Сохранённые контакты повреждены и пропущены")


def get_news() -> list[dict]:
    return _state["news"]


def get_ann() -> list[dict]:
    return _state["ann"]


def last_update() -> int | None:
    return _state["updated"]


def get_contact() -> dict:
    contact = dict(data.CONTACT)
    contact.update(_contact_overrides)
    return contact


async def set_contact(field: str, value: str) -> None:
    if field not in CONTACT_FIELDS:
        raise ValueError(f"Неизвестное поле: {field}")
    _contact_overrides[field] = value
    await db.kv_set("contact_overrides", json.dumps(_contact_overrides, ensure_ascii=False))


async def reset_contacts() -> None:
    _contact_overrides.clear()
    await db.kv_set("contact_overrides", "{}")


async def _fetch_home() -> str:
    timeout = aiohttp.ClientTimeout(total=20)
    headers = {"User-Agent": "ATU-InfoBot/1.0 (+https://atu.edu.az)"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(BASE_URL) as response:
            response.raise_for_status()
            return await response.text()


async def refresh() -> dict:
    """Обновляет новости и объявления с сайта. Возвращает {'ok', 'news', 'ann', 'error'}."""
    async with _refresh_lock:
        try:
            page = await _fetch_home()
        except Exception as exc:  # noqa: BLE001 - любая сетевая ошибка не должна ронять бота
            logger.warning("Не удалось загрузить сайт: %r", exc)
            return {"ok": False, "news": 0, "ann": 0, "error": f"{type(exc).__name__}: {exc}"}

        try:
            parsed = parse_home(page)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка разбора страницы")
            return {"ok": False, "news": 0, "ann": 0, "error": f"Ошибка разбора: {exc!r}"}

        news = parsed["news"][:MAX_ITEMS]
        ann = parsed["ann"][:MAX_ITEMS]
        if not news and not ann:
            return {
                "ok": False,
                "news": 0,
                "ann": 0,
                "error": "На странице не найдено ни новостей, ни объявлений (возможно, изменилась вёрстка сайта)",
            }

        if news:
            _state["news"] = news
        if ann:
            _state["ann"] = ann
        _state["updated"] = int(time.time())
        await db.kv_set(
            "news_cache",
            json.dumps(
                {"news": _state["news"], "ann": _state["ann"], "updated": _state["updated"]},
                ensure_ascii=False,
            ),
        )
        return {"ok": True, "news": len(news), "ann": len(ann), "error": None}
