"""SQLite-хранилище: пользователи (только ID и язык), статистика разделов, настройки.

FİN, пароли и любые персональные данные студентов здесь НЕ хранятся.
В боевой версии заменяется на PostgreSQL, интерфейс функций остаётся прежним.
"""
import asyncio
import sqlite3
import threading
import time

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    lang TEXT,
    first_seen INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    blocked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT NOT NULL,
    ts INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init(path: str) -> None:
    global _conn
    _conn = sqlite3.connect(path, check_same_thread=False)
    _conn.executescript(SCHEMA)
    _conn.execute("DELETE FROM events WHERE ts < ?", (int(time.time()) - 90 * 86400,))
    _conn.commit()


def close() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


async def _call(fn, *args):
    def run():
        with _lock:
            return fn(*args)

    return await asyncio.to_thread(run)


def _db() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("База данных не инициализирована (db.init)")
    return _conn


# ---------- пользователи и статистика ----------

def _touch_user(uid: int, section: str | None) -> None:
    now = int(time.time())
    conn = _db()
    conn.execute(
        "INSERT INTO users(id, first_seen, last_seen) VALUES(?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET last_seen = excluded.last_seen, blocked = 0",
        (uid, now, now),
    )
    if section:
        conn.execute("INSERT INTO events(section, ts) VALUES(?, ?)", (section, now))
    conn.commit()


def _set_lang(uid: int, lang: str) -> None:
    now = int(time.time())
    conn = _db()
    conn.execute(
        "INSERT INTO users(id, lang, first_seen, last_seen) VALUES(?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET lang = excluded.lang",
        (uid, lang, now, now),
    )
    conn.commit()


def _load_langs() -> dict[int, str]:
    rows = _db().execute("SELECT id, lang FROM users WHERE lang IS NOT NULL").fetchall()
    return {int(uid): lang for uid, lang in rows}


def _recipient_ids() -> list[int]:
    rows = _db().execute("SELECT id FROM users WHERE blocked = 0").fetchall()
    return [int(r[0]) for r in rows]


def _mark_blocked(uid: int) -> None:
    conn = _db()
    conn.execute("UPDATE users SET blocked = 1 WHERE id = ?", (uid,))
    conn.commit()


def _get_stats() -> dict:
    conn = _db()
    now = int(time.time())

    def one(sql: str, params: tuple = ()) -> int:
        return int(conn.execute(sql, params).fetchone()[0])

    return {
        "total": one("SELECT COUNT(*) FROM users"),
        "active_24h": one("SELECT COUNT(*) FROM users WHERE last_seen >= ?", (now - 86400,)),
        "active_7d": one("SELECT COUNT(*) FROM users WHERE last_seen >= ?", (now - 7 * 86400,)),
        "blocked": one("SELECT COUNT(*) FROM users WHERE blocked = 1"),
        "langs": {
            (lang or "?"): int(cnt)
            for lang, cnt in conn.execute("SELECT lang, COUNT(*) FROM users GROUP BY lang").fetchall()
        },
        "top_sections": [
            (section, int(cnt))
            for section, cnt in conn.execute(
                "SELECT section, COUNT(*) AS c FROM events WHERE ts >= ? GROUP BY section ORDER BY c DESC",
                (now - 7 * 86400,),
            ).fetchall()
        ],
    }


def _kv_get(key: str) -> str | None:
    row = _db().execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _kv_set(key: str, value: str) -> None:
    conn = _db()
    conn.execute(
        "INSERT INTO kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


async def touch_user(uid: int, section: str | None = None) -> None:
    await _call(_touch_user, uid, section)


async def set_lang(uid: int, lang: str) -> None:
    await _call(_set_lang, uid, lang)


async def load_langs() -> dict[int, str]:
    return await _call(_load_langs)


async def recipient_ids() -> list[int]:
    return await _call(_recipient_ids)


async def mark_blocked(uid: int) -> None:
    await _call(_mark_blocked, uid)


async def get_stats() -> dict:
    return await _call(_get_stats)


async def kv_get(key: str) -> str | None:
    return await _call(_kv_get, key)


async def kv_set(key: str, value: str) -> None:
    await _call(_kv_set, key, value)
