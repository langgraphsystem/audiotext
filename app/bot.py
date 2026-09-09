"""
Main Telegram bot application.
"""
import asyncio
import platform
import signal
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramConflictError
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

from .audio import ffmpeg_path
from .collector import scheduled_scans
from .config import settings
from .sources import tracked_accounts
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
    BotCommand(command="sources", description="Отслеживаемые аккаунты"),
    BotCommand(command="scan", description="Собрать новые публикации"),
    BotCommand(command="digest", description="Выгрузка материала"),
]

# Leftovers from a previous run: hosts like Railway restart the container
# without clearing an attached volume.
TEMP_PATTERNS = ("*.mp3", "*.m4a", "*.mp4", "*.webm", "*.mkv", "*.mov",
                 "*.opus", "*.ogg", "*.wav", "*.vtt", "*.srt", "*.txt")


def clean_workdir() -> None:
    """Remove stale media and transcripts left by a previous run."""
    if not settings.clean_workdir_on_start:
        return

    removed = 0
    for pattern in TEMP_PATTERNS:
        for path in settings.workdir.glob(pattern):
            try:
                path.unlink()
                removed += 1
            except OSError as e:
                logger.warning(f"Could not remove {path.name}: {e}")

    if removed:
        logger.info(f"🧹 Удалено временных файлов от прошлого запуска: {removed}")


def log_startup_info() -> None:
    """Log the effective configuration (without sensitive data)."""
    brand = settings.brand_name
    logger.info(f"🌙 {brand} · анализатор видеоконтента запущен")
    logger.info(
        f"🧠 Модель ИИ: {settings.model_display_name} "
        f"(backend: {settings.openai_model})"
    )
    logger.info(f"🔌 Эндпоинт API: {settings.openai_base_url or 'api.openai.com'}")
    if settings.fallback_models:
        logger.info(f"↩️ Резервные модели: {', '.join(settings.fallback_models)}")
    logger.info(f"🎤 Распознавание речи: OpenAI Audio API ({settings.stt_model})")
    if settings.stt_fallbacks:
        logger.info(f"↩️ Резервные модели распознавания: {', '.join(settings.stt_fallbacks)}")
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

    if settings.webhook_enabled:
        logger.info(f"🔗 Режим: webhook → {settings.webhook_url}")
    else:
        logger.info("🔄 Режим: polling (публичный домен не задан)")

    accounts = tracked_accounts()
    if accounts:
        logger.info(
            f"📚 Отслеживаемых аккаунтов: {len(accounts)} "
            f"({', '.join(a.label for a in accounts[:5])}"
            f"{'...' if len(accounts) > 5 else ''})"
        )
        interval = settings.source_scan_interval_hours
        logger.info(
            f"🗓 Плановый сбор: каждые {interval} ч"
            if interval > 0 else "🗓 Плановый сбор выключен"
        )
    else:
        logger.info("📚 Отслеживаемые аккаунты не заданы (SOURCE_ACCOUNTS)")

    logger.info(f"🗄 База собранного: {settings.database_path}")

    if ffmpeg_path():
        logger.info("🎬 FFmpeg найден: длинные видео будут разбиваться на части")
    else:
        logger.warning(
            "⚠️ FFmpeg не найден: длинные видео обработать не получится. "
            "Установите ffmpeg."
        )


def start_collector(bot: Bot) -> Optional[asyncio.Task]:
    """Launch the scheduled collection loop, if it is configured."""
    if settings.source_scan_interval_hours <= 0 or not settings.accounts:
        return None

    async def notify(text: str) -> None:
        if settings.admin_chat_id is None:
            return
        try:
            await bot.send_message(settings.admin_chat_id, text)
        except Exception as e:
            logger.warning(f"Не удалось отправить сводку сбора: {e}")

    return asyncio.create_task(scheduled_scans(notify))


async def stop_collector(task: Optional[asyncio.Task]) -> None:
    """Cancel the collection loop on shutdown."""
    if task is None:
        return
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass


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
    clean_workdir()

    scan_task = start_collector(bot)

    try:
        await bot.set_my_commands(BOT_COMMANDS)
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Starting bot in polling mode...")
        await dp.start_polling(bot)

    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Bot stopped")
    except TelegramConflictError:
        logger.error(
            "Конфликт getUpdates: бот уже запущен в другом месте. "
            "Оставьте один экземпляр (на Railway — одна реплика) "
            "или переключитесь на webhook."
        )
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await stop_collector(scan_task)
        await close_stt_client()
        await bot.session.close()
        logger.info("Bot shutdown complete")


async def webhook_main():
    """Run the bot in webhook mode for production deployment."""
    logger.info(f"Starting {settings.brand_name} bot in webhook mode...")

    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher()

    log_startup_info()
    clean_workdir()

    app = web.Application()

    webhook_path = settings.webhook_path
    webhook_url = settings.webhook_url
    if not webhook_url:
        logger.error(
            "Webhook-режим требует WEBHOOK_BASE_URL (или RAILWAY_PUBLIC_DOMAIN). "
            "Запускаю polling."
        )
        await bot.session.close()
        await main()
        return

    await bot.set_my_commands(BOT_COMMANDS)
    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=False,
        secret_token=settings.webhook_secret,
    )

    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=settings.webhook_secret
    ).register(app, path=webhook_path)

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


def install_signal_handlers() -> None:
    """Turn SIGTERM into KeyboardInterrupt so shutdown code runs.

    Hosting platforms (Railway among them) send SIGTERM on redeploy; without
    this the process dies before sessions are closed.
    """
    def handle(signum, _frame):
        logger.info(f"Получен сигнал {signal.Signals(signum).name}, останавливаюсь...")
        raise KeyboardInterrupt

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, handle)
        except (ValueError, OSError):  # not in main thread / unsupported
            pass


def run() -> None:
    """Pick the run mode: explicit CLI flag wins, otherwise the config decides."""
    install_signal_handlers()
    args = sys.argv[1:]

    if "--webhook" in args:
        asyncio.run(webhook_main())
    elif "--polling" in args:
        asyncio.run(main())
    elif settings.webhook_enabled:
        asyncio.run(webhook_main())
    else:
        asyncio.run(main())


if __name__ == "__main__":
    run()
