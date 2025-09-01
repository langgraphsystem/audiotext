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
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

from .config import settings
from .handlers import router
from .logger import logger

# Enable uvloop on Linux for better performance
if platform.system() == "Linux":
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop enabled for better performance")
    except ImportError:
        logger.warning("uvloop not available, using default event loop")


async def main():
    """Main bot function."""
    logger.info("Starting TikTok Content Analyzer Bot...")
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(router)
    
    # Log startup info (without sensitive data)
    logger.info("🤖 TikTok Content Analyzer Bot initialized successfully")
    logger.info(f"🧠 Primary AI model: {settings.openai_model}")
    logger.info("🔄 GPT-5 Exclusive: Pure GPT-5 processing")
    logger.info("🎤 STT engine: OpenAI Whisper API")
    logger.info(f"🔤 STT language: {settings.stt_language}")
    logger.info(f"📁 Work directory: {settings.workdir}")
    logger.info(f"⏱️ Rate limits: {settings.max_requests_per_minute}/min, {settings.max_requests_per_hour}/hour")
    logger.info(f"📊 File limits: {settings.max_file_size_mb}MB, {settings.max_audio_duration_minutes}min")
    logger.info(f"🔤 Max tokens: {settings.openai_max_tokens}")
    
    try:
        # Start polling
        logger.info("Starting bot in polling mode...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot shutdown complete")


async def webhook_main():
    """Webhook mode for production deployment."""
    logger.info("Starting TikTok Content Analyzer Bot in webhook mode...")
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(router)
    
    # Setup webhook
    app = web.Application()
    
    # Webhook endpoint
    WEBHOOK_PATH = settings.webhook_path
    base_url = settings.webhook_base_url or "https://your-domain.com"
    WEBHOOK_URL = f"{base_url}{WEBHOOK_PATH}"
    
    # Set webhook
    await bot.set_webhook(url=WEBHOOK_URL)
    
    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    # Health check endpoint
    async def health_check(request):
        return web.Response(text="OK")
    
    app.router.add_get("/healthz", health_check)
    
    # Start webhook
    logger.info(f"Webhook set to: {WEBHOOK_URL}")
    logger.info("Starting webhook server...")
    
    try:
        web.run_app(app, host=settings.webhook_host, port=settings.webhook_port)
    except KeyboardInterrupt:
        logger.info("Webhook server stopped by user")
    finally:
        await bot.session.close()
        logger.info("Webhook server shutdown complete")


if __name__ == "__main__":
    # Check if webhook mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--webhook":
        asyncio.run(webhook_main())
    else:
        asyncio.run(main())
