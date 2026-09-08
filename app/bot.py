"""
Main Telegram bot application.
"""
import asyncio
import sys
import platform
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

from .audio import ffmpeg_path
from .config import settings
from .handlers import router
from .logger import logger
from .stt_openai_api import close_client as close_stt_client

# Enable uvloop on Linux for better performance
if platform.system() == "Linux":
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop enabled for better performance")
    except ImportError:
        logger.warning("uvloop not available, using default event loop")


BOT_COMMANDS = [
    BotCommand(command="start", description="Начать работу"),
    BotCommand(command="help", description="Справка"),
]


def log_startup_info() -> None:
    """Log the effective configuration (without sensitive data)."""
    brand = settings.brand_name
    logger.info(f"🌙 {brand} · анализатор видеоконтента запущен")
    logger.info(f"🧠 Модель анализа: {settings.openai_model}")
    logger.info(f"🎤 Распознавание речи: OpenAI Audio API ({settings.stt_model})")
    logger.info(f"🔤 Язык распознавания: {settings.stt_language}")
    logger.info("🌐 Платформы: TikTok, Instagram")
    logger.info(f"📁 Рабочая директория: {settings.workdir}")
    logger.info(
        f"⏱️ Лимиты: {settings.max_requests_per_minute}/мин, "
        f"{settings.max_requests_per_hour}/час"
    )
    logger.info(
        f"📊 Ограничения медиа: до {settings.max_file_size_mb} МБ, "
        f"до {settings.max_audio_duration_minutes} мин, "
        f"куски по {settings.audio_chunk_seconds} с (лимит загрузки "
        f"{settings.max_upload_size_mb} МБ)"
    )

    if ffmpeg_path():
        logger.info("🎬 FFmpeg найден: длинные видео будут разбиваться на части")
    else:
        logger.warning(
            "⚠️ FFmpeg не найден: длинные видео обработать не получится. "
            "Установите ffmpeg."
        )


def create_dispatcher() -> Dispatcher:
    """Create the dispatcher with all routers registered."""
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp


async def main():
    """Run the bot in polling mode."""
    logger.info(f"Starting {settings.brand_name} bot...")

    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher()

    log_startup_info()

    try:
        await bot.set_my_commands(BOT_COMMANDS)
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Starting bot in polling mode...")
        await dp.start_polling(bot)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await close_stt_client()
        await bot.session.close()
        logger.info("Bot shutdown complete")


async def webhook_main():
    """Run the bot in webhook mode for production deployment."""
    logger.info(f"Starting {settings.brand_name} bot in webhook mode...")

    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher()

    log_startup_info()

    app = web.Application()

    webhook_path = settings.webhook_path
    base_url = (settings.webhook_base_url or "https://your-domain.com").rstrip("/")
    webhook_url = f"{base_url}{webhook_path}"

    await bot.set_my_commands(BOT_COMMANDS)
    await bot.set_webhook(url=webhook_url, drop_pending_updates=False)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)

    async def health_check(request):
        return web.Response(text="OK")

    app.router.add_get("/healthz", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)

    logger.info(f"Webhook set to: {webhook_url}")
    logger.info(f"Listening on {settings.webhook_host}:{settings.webhook_port}")

    try:
        await site.start()
        # Serve until cancelled
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Webhook server stopped")
    finally:
        await runner.cleanup()
        await close_stt_client()
        await bot.session.close()
        logger.info("Webhook server shutdown complete")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--webhook":
        asyncio.run(webhook_main())
    else:
        asyncio.run(main())
