"""
Telegram bot message handlers.
"""
import asyncio
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from .config import settings
from .utils import (
    SUPPORTED_URL_REGEX,
    check_audio_duration,
    cleanup_temp_files,
    collect_metadata,
    detect_platform,
    extract_supported_urls,
    get_video_info,
    platform_title,
)
from .yt_dlp_client import YtDlpClient
from .stt_engine import STTEngine
from .openai_client import OpenAIClient
from .video_processor import VideoProcessor
from .rate_limiter import rate_limiter
from .collector import Collector
from .export import write_digest
from .sources import tracked_accounts
from .storage import get_storage
from .logger import get_logger

logger = get_logger(__name__)

router = Router()

BRAND = settings.brand_name
MODEL = settings.model_display_name


class ProcessingStates(StatesGroup):
    """States for processing video links."""
    processing = State()


class StatusMessage:
    """A single message that is edited as processing advances."""

    def __init__(self, message: Message):
        self._message = message
        self._sent: Optional[Message] = None
        self._last_text: Optional[str] = None

    async def set(self, text: str) -> None:
        if text == self._last_text:
            return
        self._last_text = text
        try:
            if self._sent is None:
                self._sent = await self._message.answer(text)
            else:
                await self._sent.edit_text(text)
        except TelegramBadRequest as e:
            logger.debug(f"Status update skipped: {e}")


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    """Handle /start command."""
    welcome_text = f"""🌙 **{BRAND} — анализатор видеоконтента**
_Модель ИИ: {MODEL}_

Отправь ссылку на **TikTok** или **Instagram** видео, и я:
1. 📝 Извлеку субтитры (если доступны)
2. 🎵 Скачаю и расшифрую аудио (если субтитров нет)
3. 🧠 Проведу глубокий анализ контента

**Как использовать:**
Просто вставь ссылку, например:
`https://www.tiktok.com/@username/video/1234567890`
`https://www.instagram.com/reel/XXXXXXXXXXX/`

**🚀 Возможности {BRAND}:**
• Многоуровневый анализ контента (семантический, эмоциональный, контекстуальный)
• Профессиональные инсайты для маркетологов и создателей
• Оценка виральности и engagement потенциала
• Готовые кэпшны для социальных сетей
• Структурированные данные в JSON формате
• Длинные видео: аудио автоматически режется на части — ограничения по длине почти нет \
(до {settings.max_audio_duration_minutes} мин)

⚠️ **Правовое уведомление:** Используйте ответственно и соблюдайте Условия использования TikTok и Instagram."""

    await message.answer(welcome_text, parse_mode="Markdown")


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = f"""📖 **Справка и использование**

**Команды:**
• `/start` - Показать приветственное сообщение
• `/help` - Показать эту справку
• `/sources` - Отслеживаемые аккаунты и статистика сбора
• `/scan` - Собрать новые публикации прямо сейчас
• `/digest` - Выгрузка собранного материала файлом

**Поддерживаемые ссылки:**
• `https://www.tiktok.com/@username/video/...`
• `https://vt.tiktok.com/...`
• `https://www.instagram.com/reel/...`
• `https://www.instagram.com/p/...`
• `https://www.instagram.com/tv/...`

**Этапы обработки:**
1. **Проверка субтитров** — сначала ищем готовые субтитры
2. **Скачивание аудио** — качаем только аудиодорожку, без видео
3. **Расшифровка** — длинное аудио автоматически делится на части
4. **Анализ** — модель ИИ {MODEL} проводит глубокий многоуровневый анализ контента

**Результат:**
• 📄 Текстовый файл (субтитры или расшифровка)
• 📊 Профессиональный отчёт модели {MODEL} с инсайтами и рекомендациями

**Ограничения:**
• Длительность: до {settings.max_audio_duration_minutes} мин
• Лимиты: {settings.max_requests_per_minute} запросов/мин, {settings.max_requests_per_hour} запросов/час

**Устранение неполадок:**
• Убедитесь, что видео публичное (для закрытых Instagram-аккаунтов нужны cookies)
• Проверьте подключение к интернету
• Длинные видео обрабатываются дольше — это нормально"""

    await message.answer(help_text, parse_mode="Markdown")


# search mode: the link may appear anywhere in the message, not only at the start


def _is_admin(message: Message) -> bool:
    """Whether this chat may run collection commands."""
    if settings.admin_chat_id is None:
        return True
    return message.chat.id == settings.admin_chat_id


@router.message(F.text.startswith("/sources"))
async def cmd_sources(message: Message):
    """Show tracked accounts and what has been collected so far."""
    accounts = tracked_accounts()
    stats = get_storage().stats()

    lines = ["📚 **Сбор материала**", ""]

    if accounts:
        lines.append("**Отслеживаемые аккаунты:**")
        lines += [f"• {a.label}" for a in accounts]
    else:
        lines.append("Аккаунты не заданы — заполните `SOURCE_ACCOUNTS`.")

    lines += [
        "",
        f"**В базе:** {stats['ok']} публикаций"
        + (f" (ошибок: {stats['failed']})" if stats["failed"] else ""),
    ]

    if stats["per_account"]:
        lines.append("")
        lines += [f"• @{a} — {c}" for a, c in stats["per_account"].items()]

    if stats["last_processed_at"]:
        import time as _time
        when = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(stats["last_processed_at"]))
        lines += ["", f"Последний сбор: {when}"]

    interval = settings.source_scan_interval_hours
    lines.append(
        f"Расписание: каждые {interval} ч" if interval > 0 else "Расписание: выключено"
    )

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(F.text.startswith("/scan"))
async def cmd_scan(message: Message):
    """Run a collection pass on demand."""
    if not _is_admin(message):
        await message.answer("⛔ Команда доступна только в админском чате.")
        return

    if not tracked_accounts():
        await message.answer("❌ Список аккаунтов пуст. Заполните `SOURCE_ACCOUNTS`.")
        return

    status = StatusMessage(message)
    await status.set("🔍 Обхожу аккаунты...")

    try:
        result = await Collector().scan(progress=status.set)
        await status.set(f"✅ Сбор завершён\n\n{result.summary()}")

        if result.collected:
            await message.answer(
                "Готово. `/digest` — выгрузка материала файлом.", parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Сбор не удался: {e}")
        await status.set(f"❌ Сбор не удался: {e}")


@router.message(F.text.startswith("/digest"))
async def cmd_digest(message: Message):
    """Send the collected material as one file."""
    parts = (message.text or "").split()
    limit = 20
    if len(parts) > 1 and parts[1].isdigit():
        limit = max(1, min(200, int(parts[1])))

    stats = get_storage().stats()
    if not stats["ok"]:
        await message.answer(
            "📭 База пуста. Запустите `/scan` или отправьте ссылку.", parse_mode="Markdown"
        )
        return

    await message.answer(f"📦 Собираю выгрузку по последним {limit} публикациям...")

    try:
        path = await asyncio.to_thread(write_digest, limit)
        document = FSInputFile(path, filename=path.name)
        await message.answer_document(
            document,
            caption=(
                "🗂 Материал для производства контента.\n"
                "Откройте файл в приложении Claude и попросите подготовить сценарии."
            ),
        )
        cleanup_temp_files(path)
    except Exception as e:
        logger.error(f"Выгрузка не удалась: {e}")
        await message.answer(f"❌ Не удалось собрать выгрузку: {e}")


@router.message(F.text.regexp(SUPPORTED_URL_REGEX, mode="search"))
async def handle_video_url(message: Message, state: FSMContext):
    """Handle TikTok and Instagram URL messages."""
    user_id = message.from_user.id

    allowed, error_msg = rate_limiter.is_allowed(user_id)
    if not allowed:
        await message.answer(f"⏱️ {error_msg}")
        return

    urls = extract_supported_urls(message.text or "")
    if not urls:
        await message.answer("❌ В вашем сообщении не найдено ссылок на TikTok или Instagram.")
        return

    url = urls[0]
    platform = detect_platform(url)
    source = platform_title(platform)
    logger.info(f"Processing {source} URL: {url[-12:]} from user {user_id}")

    status = StatusMessage(message)
    temp_files = []
    openai_client = None

    await state.set_state(ProcessingStates.processing)

    try:
        await status.set(f"🔄 Обрабатываю видео из {source}...")

        video_info = await asyncio.to_thread(get_video_info, url)
        if video_info is None:
            await status.set(
                f"❌ Не удалось получить данные видео из {source}. "
                "Проверьте, что ссылка верная и запись публичная."
            )
            return

        if not check_audio_duration(video_info):
            duration_min = (video_info.get('duration') or 0) / 60
            await status.set(
                f"❌ Видео слишком длинное ({duration_min:.1f} мин). "
                f"Максимальная длительность: {settings.max_audio_duration_minutes} мин."
            )
            return

        metadata = collect_metadata(video_info)
        if metadata:
            logger.info(f"Метаданные публикации: {', '.join(metadata.keys())}")

        try:
            yt_client = YtDlpClient()
            stt_engine = STTEngine()
            openai_client = OpenAIClient()
            processor = VideoProcessor(yt_client, stt_engine, openai_client)
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            await status.set("❌ Ошибка инициализации системы. Попробуйте позже.")
            return

        text_content = None
        segments = None
        txt_path = None

        # Step 1: try subtitles
        await status.set("📝 Проверяю субтитры...")
        try:
            text_content, subtitle_temp_files = await processor.extract_subtitles(url)
            temp_files.extend(subtitle_temp_files)
            if text_content:
                await status.set("✅ Субтитры найдены, готовлю текст...")
        except Exception as e:
            logger.error(f"Error extracting subtitles: {e}")

        # Step 2: audio + transcription
        if not text_content:
            await status.set("🎵 Субтитров нет. Скачиваю аудиодорожку...")

            async def progress(index: int, total: int) -> None:
                if total > 1:
                    await status.set(f"🎤 Расшифровываю аудио: часть {index} из {total}...")
                else:
                    await status.set("🎤 Расшифровываю аудио...")

            # A failure here is not fatal: frames and publication data still
            # carry the clip, and many reels have no speech at all.
            try:
                text_content, segments, audio_temp_files = await processor.extract_audio_transcript(
                    url, progress=progress
                )
                temp_files.extend(audio_temp_files)

                if not text_content:
                    logger.info("Речь не распознана — продолжаю с визуальным разбором")
            except ValueError as e:
                logger.warning(f"Аудио пропущено: {e}")
                await status.set(f"⚠️ {e}\nПродолжаю по кадрам...")
            except Exception as e:
                logger.warning(f"Расшифровка не удалась, продолжаю по кадрам: {e}")
                await status.set("⚠️ Речь получить не удалось. Разбираю по кадрам...")

        for file in temp_files:
            if file.suffix == '.txt':
                txt_path = file
                break

        # Visual pass: key frames go to the model together with the transcript
        images = []
        if settings.vision_enabled:
            await status.set("🖼 Разбираю кадры видео...")
            images, visual_temp_files = await processor.collect_visual_context(url, video_info)
            temp_files.extend(visual_temp_files)

        has_text = bool(text_content and len(text_content.strip()) >= 10)
        if not has_text and not images:
            await status.set(
                "❌ Не удалось извлечь ни речь, ни кадры из видео. "
                "Проверьте, что запись публичная и доступна."
            )
            return

        # Step 3: send extracted text
        if txt_path is not None and has_text:
            try:
                document = FSInputFile(txt_path, filename=f"{platform or 'video'}_content.txt")
                await message.answer_document(
                    document, caption=f"📄 Извлечённый контент из {source}"
                )
            except TelegramBadRequest as e:
                logger.warning(f"Failed to send document: {e}")

        # Step 4: analysis
        await status.set(f"🧠 Модель {MODEL} анализирует контент...")

        try:
            analysis, analysis_path = await processor.analyze_content(
                text_content or "",
                segments,
                platform=platform,
                metadata=metadata,
                images=images,
            )
            if analysis_path:
                temp_files.append(analysis_path)

            if not analysis or not analysis.strip():
                await status.set(
                    "❌ Получен пустой ответ анализа. Попробуйте другой ролик или повторите позже."
                )
                return

            await status.set("🎉 Анализ завершён!")

            sent_as_file = False
            if analysis_path is not None:
                try:
                    document = FSInputFile(
                        analysis_path, filename=f"{BRAND.replace(' ', '_')}_Analysis.txt"
                    )
                    await message.answer_document(
                        document,
                        caption=f"🌙 Профессиональный анализ | {BRAND} · модель {MODEL} · {source}",
                    )
                    sent_as_file = True
                except TelegramBadRequest as e:
                    logger.warning(f"Failed to send analysis document: {e}")

            if not sent_as_file:
                await message.answer("📊 Анализ:")
                for chunk in processor.send_analysis_chunks(analysis):
                    await message.answer(chunk)

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            await status.set(f"❌ Ошибка при анализе контента: {e}")
            return

        logger.info(f"Successfully processed {source} video for user {user_id}")

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await message.answer(f"❌ Ошибка при обработке видео: {e}")

    finally:
        cleanup_temp_files(*temp_files)
        if openai_client:
            try:
                await openai_client.close()
            except Exception:
                pass
        await state.clear()


@router.message()
async def handle_other_messages(message: Message):
    """Handle other messages."""
    await message.answer(
        f"🌙 Отправь мне ссылку на видео из TikTok или Instagram, "
        f"и {BRAND} сделает профессиональный анализ!\n\n"
        "Используй /help для получения дополнительной информации."
    )
