import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import content
import db
import notifier
from admin import admin_router
from admin_texts import at
from bot_profile import setup_profile
from config import ADMIN_IDS, BOT_TOKEN, DB_PATH, NEWS_REFRESH_MINUTES
from handlers import router
from middleware import StatsMiddleware, ThrottlingMiddleware
from store import USER_LANG, get_lang

logger = logging.getLogger(__name__)


async def news_loop(bot: Bot) -> None:
    """Периодически обновляет новости и объявления с сайта университета."""
    failures = 0
    while True:
        try:
            result = await content.refresh()
        except Exception as exc:  # noqa: BLE001 - цикл не должен останавливаться
            logger.exception("Сбой автообновления новостей")
            result = {"ok": False, "error": repr(exc)}
        if result["ok"]:
            failures = 0
            logger.info("Новости обновлены: %s новостей, %s объявлений", result["news"], result["ann"])
        else:
            failures += 1
            logger.warning("Автообновление не удалось (%s подряд): %s", failures, result["error"])
            if failures == 3:  # один раз сообщаем администраторам, без спама
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(admin_id, at(get_lang(admin_id), "news_fail_alert"))
                    except Exception:  # noqa: BLE001
                        logger.warning("Не удалось уведомить администратора %s", admin_id)
        await asyncio.sleep(NEWS_REFRESH_MINUTES * 60)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    db.init(DB_PATH)
    USER_LANG.update(await db.load_langs())
    await content.load()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    throttle = ThrottlingMiddleware(limit=10, window=10.0, exempt=ADMIN_IDS)
    dp.message.outer_middleware(throttle)
    dp.callback_query.outer_middleware(throttle)
    dp.message.outer_middleware(StatsMiddleware())
    dp.include_router(admin_router)  # админ-панель должна идти раньше основного роутера
    dp.include_router(router)

    await setup_profile(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    background_tasks: set[asyncio.Task] = set()

    def on_new_items(items: list[dict]) -> None:
        task = asyncio.create_task(notifier.notify_new_items(bot, items))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    content.set_new_items_handler(on_new_items)

    news_task = asyncio.create_task(news_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        news_task.cancel()
        await bot.session.close()
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
