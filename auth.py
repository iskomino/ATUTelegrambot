"""Демо-авторизация студента по FİN и паролю.

ВАЖНО: это ТЕСТОВЫЕ данные. Реальные пароли студентов бот хранить НЕ должен.
В боевой версии проверка выполняется на стороне университетской системы (LMS/API),
а бот получает только результат и данные, на которые у студента есть право.
"""
import hashlib
import hmac
import re

FIN_RE = re.compile(r"[A-Z0-9]{7}")

DEMO_FIN = "1DEMO01"
DEMO_PASSWORD = "Demo#2026"

_SALT = b"atu-demo-salt"


def _hash(password: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _SALT, 100_000)


MOCK_STUDENTS: dict[str, dict] = {
    DEMO_FIN: {
        "hash": _hash(DEMO_PASSWORD),
        "name": {"az": "Test Tələbə", "ru": "Тестовый студент", "en": "Test Student"},
        "faculty_index": 2,  # Rəqəmsal texnologiyalar
        "specialty": {
            "az": "İnformasiya texnologiyaları",
            "ru": "Информационные технологии",
            "en": "Information Technologies",
        },
        "course": 2,
        "group": "IT-201",
        "gpa": "84.5",
        "grades": [
            ({"az": "Proqramlaşdırma", "ru": "Программирование", "en": "Programming"}, 92),
            ({"az": "Verilənlər bazası", "ru": "Базы данных", "en": "Databases"}, 85),
            ({"az": "Diskret riyaziyyat", "ru": "Дискретная математика", "en": "Discrete Mathematics"}, 78),
            ({"az": "Kompüter şəbəkələri", "ru": "Компьютерные сети", "en": "Computer Networks"}, 83),
        ],
    }
}

_DUMMY_HASH = _hash("dummy-password-for-constant-time")


def authenticate(fin: str, password: str) -> dict | None:
    """Возвращает данные студента или None. Время проверки не зависит от наличия FİN."""
    student = MOCK_STUDENTS.get(fin)
    expected = student["hash"] if student else _DUMMY_HASH
    ok = hmac.compare_digest(_hash(password), expected)
    return student if (student and ok) else None


def get_student(fin: str) -> dict | None:
    return MOCK_STUDENTS.get(fin)
