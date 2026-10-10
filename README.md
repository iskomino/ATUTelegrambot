# ATU Telegram Bot (демо)

## Запуск
```bash
python -m venv venv
venv\Scripts\activate           # Windows (Mac/Linux: source venv/bin/activate)
python -m pip install -r requirements.txt
copy .env.example .env          # впишите BOT_TOKEN (и ADMIN_IDS для админ-панели)
python main.py
```

## Админ-панель
1. Узнайте свой Telegram ID у бота @userinfobot.
2. Впишите его в `.env`: `ADMIN_IDS=123456789` (несколько ID через запятую).
3. Перезапустите бота и отправьте ему `/admin`.

Возможности: статистика, рассылка, обновление новостей вручную, правка контактов.

## Структура
- `main.py` — запуск, фоновое автообновление новостей
- `config.py` — настройки из .env
- `texts.py` — все тексты пользователя (az / ru / en)
- `data.py` — исходные данные университета
- `content.py` — актуальные новости/объявления/контакты
- `site_parser.py` — разбор главной страницы atu.edu.az
- `db.py` — SQLite (файл bot.db): ID, язык, статистика разделов, настройки
- `admin.py` — админ-панель (язык панели = выбранный язык бота)
- `admin_texts.py` — тексты админ-панели (az / ru / en)
- `middleware.py` — сбор статистики
- `auth.py` — ДЕМО-вход по FİN (тестовый аккаунт)
- `store.py`, `keyboards.py`, `handlers.py`
