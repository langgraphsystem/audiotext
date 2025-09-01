"""
Telegram bot message handlers.
"""
import asyncio
from pathlib import Path
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from .config import settings
from .utils import is_tiktok_url, cleanup_temp_files, check_audio_duration, get_video_info
from .yt_dlp_client import YtDlpClient
from .stt_engine import STTEngine
from .openai_client import OpenAIClient
from .video_processor import VideoProcessor
from .rate_limiter import rate_limiter
from .logger import get_logger

logger = get_logger(__name__)

router = Router()


class ProcessingStates(StatesGroup):
    """States for processing TikTok videos."""
    processing = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    """Handle /start command."""
    welcome_text = """🤖 **Профессиональный TikTok Анализатор контента**
*Powered by GPT-5*

Отправь мне ссылку на TikTok видео, и я:
1. 📝 Извлеку субтитры (если доступны)
2. 🎵 Скачаю и расшифрую аудио (если нет субтитров)  
3. 🧠 Проведу глубокий анализ с помощью GPT-5

**Как использовать:**
Просто вставь TikTok URL, например:
`https://www.tiktok.com/@username/video/1234567890`

**🚀 Возможности GPT-5:**
• Многоуровневый анализ контента (семантический, эмоциональный, контекстуальный)
• Профессиональные инсайты для маркетологов и создателей
• Оценка виральности и engagement потенциала
• Готовые кэпшны для социальных сетей
• Структурированные данные в JSON формате
• Персонализированные рекомендации

⚠️ **Правовое уведомление:** Используйте ответственно и соблюдайте Условия использования TikTok."""
    
    await message.answer(welcome_text, parse_mode="Markdown")


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """📖 **Справка и использование**

**Команды:**
• `/start` - Показать приветственное сообщение
• `/help` - Показать эту справку

**Поддерживаемые URL:**
• `https://www.tiktok.com/@username/video/...`
• `https://vt.tiktok.com/...`

**Этапы обработки:**
1. **Проверка субтитров** - Сначала пытается найти существующие субтитры
2. **Скачивание аудио** - Скачивает аудио лучшего качества, если нет субтитров
3. **Расшифровка** - Использует Whisper AI для преобразования речи в текст
4. **Анализ** - GPT-5 проводит глубокий многоуровневый анализ контента

**Результат:**
• 📄 Текстовый файл (субтитры или расшифровка)
• 📊 Профессиональный анализ от GPT-5 с инсайтами, метриками и рекомендациями

**Устранение неполадок:**
• Убедитесь, что TikTok видео публичное
• Проверьте подключение к интернету
• Большие видео могут обрабатываться дольше

При проблемах проверьте логи бота или попробуйте с другим видео."""
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(F.text.regexp(r"(https?://)?(www\.)?(vt\.)?tiktok\.com"))
async def handle_tiktok_url(message: Message, state: FSMContext):
    """Handle TikTok URL messages."""
    user_id = message.from_user.id
    
    # Check rate limiting
    allowed, error_msg = rate_limiter.is_allowed(user_id)
    if not allowed:
        await message.answer(f"⏱️ {error_msg}")
        return
    
    text = message.text.strip()
    
    # Extract URLs from message
    urls = [word for word in text.split() if is_tiktok_url(word)]
    
    if not urls:
        await message.answer("❌ В вашем сообщении не найдено действительных TikTok ссылок.")
        return
    
    # Process the first URL found
    url = urls[0]
    logger.info(f"Processing TikTok URL: {url[-8:]} from user {user_id}")
    
    # Check video duration before processing
    video_info = await asyncio.to_thread(get_video_info, url)
    if video_info and not check_audio_duration(video_info):
        duration_min = video_info.get('duration', 0) / 60
        await message.answer(f"❌ Видео слишком длинное ({duration_min:.1f} мин). Максимальная длительность: {settings.max_audio_duration_minutes} мин.")
        return
    
    # Set processing state
    await state.set_state(ProcessingStates.processing)
    
    try:
        # Send processing message
        processing_msg = await message.answer("🔄 Обрабатываю TikTok видео...")
        
        # Initialize clients
        yt_client = None
        stt_engine = None
        openai_client = None
        
        try:
            yt_client = YtDlpClient()
            stt_engine = STTEngine()
            openai_client = OpenAIClient()
            processor = VideoProcessor(yt_client, stt_engine, openai_client)
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            await message.answer("❌ Ошибка инициализации системы. Попробуйте позже.")
            return
        
        text_content = None
        segments = None
        temp_files = []
        txt_path = None
        
        # Step 1: Try to get subtitles
        await message.answer("📝 Проверяю субтитры...")
        try:
            text_content, subtitle_temp_files = await processor.extract_subtitles(url)
            temp_files.extend(subtitle_temp_files)
            
            if text_content:
                await message.answer("✅ Субтитры найдены! Конвертирую в текст...")
                # Find the txt file in temp_files
                for file in temp_files:
                    if file.suffix == '.txt':
                        txt_path = file
                        break
        except Exception as e:
            logger.error(f"Error extracting subtitles: {e}")
        
        if not text_content:
            # Step 2: Download audio and transcribe
            await message.answer("🎵 Субтитры не найдены. Скачиваю аудио...")
            try:
                text_content, segments, audio_temp_files = await processor.extract_audio_transcript(url)
                temp_files.extend(audio_temp_files)
                
                if not text_content:
                    await message.answer("❌ Не удалось скачать аудио. Проверьте, доступно ли видео.")
                    return
                
                await message.answer("🎤 Расшифровываю аудио с помощью Whisper AI...")
                # Find the txt file in temp_files
                for file in temp_files:
                    if file.suffix == '.txt':
                        txt_path = file
                        break
                        
            except ValueError as e:
                await message.answer(f"❌ {str(e)}")
                return
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await message.answer("❌ Ошибка при обработке аудио.")
                return
        
        if not text_content or len(text_content.strip()) < 10:
            await message.answer("❌ Не удалось извлечь осмысленный текст из видео.")
            return
        
        # Step 3: Send text file
        await message.answer("📄 Отправляю текстовый файл...")
        try:
            document = FSInputFile(txt_path, filename=f"tiktok_content.txt")
            await message.answer_document(document, caption="📄 Извлеченный контент из TikTok видео")
        except TelegramBadRequest as e:
            logger.warning(f"Failed to send document: {e}")
            await message.answer("📄 Текстовый контент успешно извлечен!")
        
        # Step 4: GPT-5 Analysis
        await message.answer("🧠 Запускаю GPT-5 для глубокого анализа контента...")
        
        if not openai_client:
            await message.answer("❌ GPT-5 клиент недоступен.")
            return
        
        try:
            analysis, analysis_path = await processor.analyze_content(text_content, segments)
            if analysis_path:
                temp_files.append(analysis_path)

            # Step 5: Send analysis
            if not analysis or not analysis.strip():
                await message.answer("❌ Получен пустой ответ от модели. Попробуйте другой ролик или повторите позже.")
            elif analysis_path is not None:
                await message.answer("🎉 Анализ завершен! Отправляю профессиональный отчет...")
                try:
                    document = FSInputFile(analysis_path, filename="GPT_TikTok_Analysis.txt")
                    await message.answer_document(document, caption="🧠 Профессиональный анализ | TikTok Content Intelligence")
                except TelegramBadRequest as e:
                    logger.warning(f"Failed to send analysis document: {e}")
                    await message.answer("📊 Анализ (в сообщениях):")
                    chunks = processor.send_analysis_chunks(analysis)
                    for chunk in chunks:
                        await message.answer(chunk)
            else:
                # No file created; send chunks as messages
                await message.answer("📊 Анализ (в сообщениях):")
                chunks = processor.send_analysis_chunks(analysis)
                for chunk in chunks:
                    await message.answer(chunk)
        except Exception as e:
            logger.error(f"Error during GPT-5 analysis: {e}")
            await message.answer("❌ Ошибка при работе с GPT-5. Попробуйте позже.")
        
        # Cleanup
        cleanup_temp_files(*temp_files)
        if openai_client:
            try:
                await openai_client.close()
            except Exception:
                pass
        
        logger.info(f"Successfully processed TikTok video for user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error processing TikTok video: {e}")
        await message.answer(f"❌ Ошибка при обработке видео: {str(e)}")
        
        # Cleanup on error
        try:
            cleanup_temp_files(*temp_files)
            if openai_client:
                try:
                    await openai_client.close()
                except Exception:
                    pass
        except:
            pass
    
    finally:
        # Clear processing state
        await state.clear()


@router.message()
async def handle_other_messages(message: Message):
    """Handle other messages."""
    await message.answer(
        "🤖 Отправь мне ссылку на TikTok видео для профессионального анализа GPT-5!\n\n"
        "Используй /help для получения дополнительной информации."
    )

