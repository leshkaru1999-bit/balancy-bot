import asyncio
import logging
from datetime import datetime, timezone, timedelta
from aiogram import Bot
from bot.services import db
import bot.config as cfg

logger = logging.getLogger(__name__)

async def run_notifier(bot: Bot):
    logger.info("⏰ Планировщик уведомлений запущен")
    while True:
        try:
            # Получаем текущее время по Ташкенту (UTC+5)
            now_tashkent = datetime.now(timezone(timedelta(hours=5)))
            time_str = now_tashkent.strftime("%H:%M")
            
            # Проверяем только в начале минуты (чтобы не дублировать)
            if now_tashkent.second < 10:
                user_ids = await db.get_users_for_reminder(time_str)
                for uid in user_ids:
                    try:
                        await bot.send_message(uid, "🔔 Напоминание! Не забудьте записать свои расходы за сегодня. Просто отправьте голосовое сообщение! 🎙")
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление пользователю {uid}: {e}")
            
            # Спим до следующего интервала (проверяем каждые 10 секунд)
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Ошибка в планировщике уведомлений: {e}")
            await asyncio.sleep(60)
