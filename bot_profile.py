"""Оформление бота в Telegram: описание, краткое описание и команды на языке пользователя.

Тексты видны ещё до нажатия /start. Пока проект не утверждён университетом, в них стоит
пометка «демо-версия»; после утверждения её можно убрать здесь же.
Лимиты Telegram: описание до 512 символов, краткое до 120, описание команды до 256.
"""
import logging

from aiogram import Bot
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_LANG = "az"

DESCRIPTION = {
    "az": """🎓 ATU tələbələri və abituriyentləri üçün rəqəmsal köməkçi!

Fakültələr, qəbul, dərs cədvəlləri, xəbərlər, elanlar və əlaqə məlumatları, hamısı bir toxunuşla.

🔔 Yeni xəbərlərə abunə olun və universitetdə baş verənləri ilk siz öyrənin
🗓 Dərs cədvəlini dərhal əldə edin
🌐 Azərbaycan, rus və ingilis dilləri

Başlamaq üçün /start düyməsini basın!""",
    "ru": "Информационный бот для Азербайджанского технологического университета (демо-версия). Факультеты, поступление, новости и объявления, расписание занятий, контакты. Можно подписаться на новые новости. Нажмите /start, чтобы начать.",
    "en": "Information bot for Azerbaijan Technology University (demo version). Faculties, admission, news and announcements, class schedules and contacts. You can subscribe to new-news notifications. Press /start to begin.",
}

SHORT_DESCRIPTION = {
    "az": "ATU üçün rəqəmsal köməkçi: fakültələr, qəbul, xəbərlər, cədvəl və yeni xəbər bildirişləri 🎓",
    "ru": "Информационный бот АТУ (демо): факультеты, поступление, новости, расписание",
    "en": "ATU information bot (demo): faculties, admission, news, schedules",
}

COMMANDS = {
    "az": [("start", "Başla"), ("menu", "Əsas menyu"), ("help", "Kömək"), ("cancel", "Ləğv et")],
    "ru": [("start", "Начать"), ("menu", "Главное меню"), ("help", "Помощь"), ("cancel", "Отмена")],
    "en": [("start", "Start"), ("menu", "Main menu"), ("help", "Help"), ("cancel", "Cancel")],
}


async def setup_profile(bot: Bot) -> None:
    """Применяет оформление. Каждый вызов независим: сбой одного (например, лимит Telegram)
    не мешает остальным и не мешает запуску бота."""
    for lang_code, texts_lang in [(None, DEFAULT_PROFILE_LANG), ("az", "az"), ("ru", "ru"), ("en", "en")]:
        label = lang_code or "по умолчанию"
        calls = {
            "описание": lambda: bot.set_my_description(description=DESCRIPTION[texts_lang], language_code=lang_code),
            "краткое описание": lambda: bot.set_my_short_description(
                short_description=SHORT_DESCRIPTION[texts_lang], language_code=lang_code
            ),
            "команды": lambda: bot.set_my_commands(
                [BotCommand(command=c, description=d) for c, d in COMMANDS[texts_lang]], language_code=lang_code
            ),
        }
        for what, call in calls.items():
            try:
                await call()
            except Exception:  # noqa: BLE001
                logger.exception("Не удалось обновить профиль бота: %s (язык %s)", what, label)