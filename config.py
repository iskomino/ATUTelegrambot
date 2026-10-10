import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Создайте файл .env по образцу .env.example")

ADMIN_IDS: list[int] = [
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()
]

try:
    NEWS_REFRESH_MINUTES: int = max(5, int(os.getenv("NEWS_REFRESH_MINUTES", "30")))
except ValueError:
    NEWS_REFRESH_MINUTES = 30

DB_PATH: str = os.getenv("DB_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")
