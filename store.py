"""Временное хранилище для демо (в памяти).

В боевой версии заменяется на PostgreSQL/Redis, интерфейс функций остаётся тем же.
"""
import time

from texts import DEFAULT_LANG

USER_LANG: dict[int, str] = {}
SESSIONS: dict[int, dict] = {}
ATTEMPTS: dict[int, dict] = {}

SESSION_TTL = 15 * 60  # сессия кабинета: 15 минут неактивности
MAX_ATTEMPTS = 5
LOCK_SECONDS = 5 * 60


def get_lang(uid: int) -> str:
    return USER_LANG.get(uid, DEFAULT_LANG)


def start_session(uid: int, fin: str) -> None:
    SESSIONS[uid] = {"fin": fin, "exp": time.time() + SESSION_TTL}


def get_session(uid: int) -> dict | None:
    session = SESSIONS.get(uid)
    if not session:
        return None
    if session["exp"] < time.time():
        SESSIONS.pop(uid, None)
        return None
    session["exp"] = time.time() + SESSION_TTL
    return session


def end_session(uid: int) -> None:
    SESSIONS.pop(uid, None)


def lock_remaining(uid: int) -> int:
    """Сколько секунд осталось до конца блокировки (0 — не заблокирован)."""
    rec = ATTEMPTS.get(uid)
    if not rec:
        return 0
    return max(0, int(rec["lock_until"] - time.time()))


def register_failure(uid: int) -> int:
    """Фиксирует неудачную попытку входа. Возвращает число оставшихся попыток."""
    rec = ATTEMPTS.setdefault(uid, {"count": 0, "lock_until": 0.0})
    rec["count"] += 1
    if rec["count"] >= MAX_ATTEMPTS:
        rec["lock_until"] = time.time() + LOCK_SECONDS
        rec["count"] = 0
        return 0
    return MAX_ATTEMPTS - rec["count"]


def reset_attempts(uid: int) -> None:
    ATTEMPTS.pop(uid, None)
