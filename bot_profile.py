"""Оформление бота в Telegram: описание, краткое описание (только на азербайджанском) и команды.

Описание и «About» одинаковы для всех пользователей. Отдельные версии для русского и английского
языков Telegram удаляются (пустая строка), поэтому остаётся один азербайджанский текст.
Команды в меню бота показываются на языке пользователя (az / ru / en).
Лимиты Telegram: описание до 512 символов, краткое до 120, описание команды до 256.
"""
import logging

from aiogram import Bot
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)

DESCRIPTION = {
    "az": """🎓 ATU tələbələri və abituriyentləri üçün rəqəmsal köməkçi!

Fakültələr, qəbul, dərs cədvəlləri, xəbərlər, elanlar və əlaqə məlumatları, hamısı bir toxunuşla.

🔔 Yeni xəbərlərə abunə olun və universitetdə baş verənləri ilk siz öyrənin
🗓 Dərs cədvəlini dərhal əldə edin
🌐 Azərbaycan, rus və ingilis dilləri

Başlamaq üçün /start düyməsini basın!""",
}

SHORT_DESCRIPTION = {
    "az": "ATU üçün rəqəmsal köməkçi: fakültələr, qəbul, xəbərlər, cədvəl və yeni xəbər bildirişləri 🎓",
}

COMMANDS = {
    "az": [("start", "Başla"), ("menu", "Əsas menyu"), ("help", "Kömək"), ("cancel", "Ləğv et")],
    "ru": [("start", "Начать"), ("menu", "Главное меню"), ("help", "Помощь"), ("cancel", "Отмена")],
    "en": [("start", "Start"), ("menu", "Main menu"), ("help", "Help"), ("cancel", "Cancel")],
}

# Языки Telegram, для которых отдельное описание удаляется (показывается общий азербайджанский текст)
REMOVE_DEDICATED_FOR = ("ru", "en")


async def setup_profile(bot: Bot) -> None:
    """Применяет оформление. Каждый вызов независим: сбой одного (например, лимит Telegram)
    не мешает остальным и не мешает запуску бота."""
    description, short = DESCRIPTION["az"], SHORT_DESCRIPTION["az"]
    calls: list[tuple[str, object]] = []

    # общий текст: по умолчанию и для азербайджанского языка
    for code in (None, "az"):
        label = code or "по умолчанию"
        calls.append((f"описание ({label})", lambda c=code: bot.set_my_description(description=description, language_code=c)))
        calls.append((f"краткое описание ({label})", lambda c=code: bot.set_my_short_description(short_description=short, language_code=c)))

    # удаляем отдельные версии для других языков (пустая строка), чтобы не показывались старые тексты
    for code in REMOVE_DEDICATED_FOR:
        calls.append((f"описание ({code}): удаление", lambda c=code: bot.set_my_description(description="", language_code=c)))
        calls.append((f"краткое описание ({code}): удаление", lambda c=code: bot.set_my_short_description(short_description="", language_code=c)))

    # команды на языке пользователя
    for code in (None, "az", "ru", "en"):
        texts_lang = code or "az"
        label = code or "по умолчанию"
        commands = [BotCommand(command=c, description=d) for c, d in COMMANDS[texts_lang]]
        calls.append((f"команды ({label})", lambda c=code, cmds=commands: bot.set_my_commands(cmds, language_code=c)))

    for what, call in calls:
        try:
            await call()
        except Exception:  # noqa: BLE001
            logger.exception("Не удалось обновить профиль бота: %s", what)