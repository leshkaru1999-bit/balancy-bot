import asyncio
import logging
import uvicorn
import aiohttp

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import bot.config as cfg
from bot.models.database import init_db
from bot.handlers import commands, voice, callbacks, manual, payments

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def get_ngrok_url() -> str | None:
    """Автоматически читает публичный URL из локального ngrok агента."""
    try:
        timeout = aiohttp.ClientTimeout(total=2)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("http://localhost:4040/api/tunnels") as r:
                data = await r.json()
                for tunnel in data.get("tunnels", []):
                    if tunnel.get("proto") == "https":
                        return tunnel["public_url"]
    except Exception:
        pass
    return None


async def run_api():
    """Запускает FastAPI сервер."""
    from bot.api.server import app
    config = uvicorn.Config(
        app,
        host=cfg.API_HOST,
        port=cfg.API_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    await server.serve()


def get_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(manual.router)
    dp.include_router(voice.router)
    dp.include_router(payments.router)
    return dp


async def main():
    # 1. Инициализируем БД
    logger.info("💾 Инициализация базы данных...")
    await init_db()
    logger.info("✅ База данных готова")

    # 2. Авто-определение ngrok URL (если запущен)
    if not cfg.MINIAPP_URL:
        ngrok_url = await get_ngrok_url()
        if ngrok_url:
            cfg.MINIAPP_URL = ngrok_url + "/miniapp"
            logger.info(f"🌐 Ngrok обнаружен! MINIAPP_URL = {cfg.MINIAPP_URL}")
        else:
            logger.warning("⚠️  Ngrok не обнаружен. Запусти: ngrok http 8000")
            logger.warning("   Mini App кнопка в боте НЕ будет отображаться.")
    else:
        logger.info(f"🌐 MINIAPP_URL = {cfg.MINIAPP_URL}")

    logger.info(f"🖥  API + Mini App: http://localhost:{cfg.API_PORT}/miniapp")

    # 3. Настройка Bot и Dispatcher
    bot = Bot(
        token=cfg.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = get_dispatcher()
    
    # 4. Передаем их в FastAPI
    from bot.api.server import app
    app.state.bot = bot
    app.state.dp = dp

    from bot.services.notifier import run_notifier
    
    # 5. Запуск
    if cfg.WEBHOOK_URL:
        # Режим Webhooks
        webhook_endpoint = f"{cfg.WEBHOOK_URL.rstrip('/')}/webhook"
        logger.info(f"🔗 Установка Webhook: {webhook_endpoint}")
        await bot.set_webhook(webhook_endpoint, allowed_updates=["message", "callback_query"])
        
        # В режиме Webhooks нам не нужен dp.start_polling, обновления будет принимать FastAPI
        await asyncio.gather(run_api(), run_notifier(bot))
    else:
        # Режим Polling (локальный запуск)
        logger.info("📡 Удаление Webhook и запуск Polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.gather(run_api(), dp.start_polling(bot, allowed_updates=["message", "callback_query"]), run_notifier(bot))


if __name__ == "__main__":
    asyncio.run(main())
