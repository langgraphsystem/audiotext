"""
Scheduled collection: walk the tracked accounts and process new posts.

Reuses the same pipeline as a manually sent link — subtitles or speech,
key frames, publication metadata — and stores the result so that content
can later be produced from the accumulated material.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List, Optional

from .config import settings
from .logger import get_logger
from .openai_client import OpenAIClient
from .sources import Account, PostRef, list_recent_posts, tracked_accounts
from .storage import get_storage
from .stt_engine import STTEngine
from .utils import cleanup_temp_files, collect_metadata, get_video_info
from .video_processor import VideoProcessor
from .yt_dlp_client import YtDlpClient

logger = get_logger(__name__)

ProgressCallback = Optional[Callable[[str], Awaitable[None]]]


@dataclass
class ScanResult:
    """What one pass over the tracked accounts produced."""
    accounts: int = 0
    seen: int = 0
    collected: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    @property
    def duration(self) -> float:
        return time.time() - self.started_at

    def summary(self) -> str:
        lines = [
            f"Аккаунтов: {self.accounts}",
            f"Просмотрено публикаций: {self.seen}",
            f"Собрано новых: {self.collected}",
            f"Уже было: {self.skipped}",
        ]
        if self.failed:
            lines.append(f"Не удалось: {self.failed}")
        lines.append(f"Заняло: {self.duration / 60:.1f} мин")
        return "\n".join(lines)


class Collector:
    """Collects new posts from tracked accounts."""

    def __init__(self):
        self.storage = get_storage()

    async def scan(self, progress: ProgressCallback = None) -> ScanResult:
        """Walk every tracked account once."""
        accounts = tracked_accounts()
        result = ScanResult(accounts=len(accounts))

        if not accounts:
            logger.info("Список отслеживаемых аккаунтов пуст (SOURCE_ACCOUNTS)")
            return result

        yt_client = YtDlpClient()
        stt_engine = STTEngine()
        openai_client = OpenAIClient()
        processor = VideoProcessor(yt_client, stt_engine, openai_client)

        try:
            for account in accounts:
                if progress:
                    await progress(f"🔍 {account.label}")

                posts = await asyncio.to_thread(list_recent_posts, account)
                result.seen += len(posts)

                known = self.storage.known_urls([p.url for p in posts])
                fresh = [p for p in posts if p.url not in known]
                result.skipped += len(posts) - len(fresh)

                for post in fresh:
                    if progress:
                        await progress(f"⬇️ {account.label}: {post.title[:40] or post.post_id}")
                    ok = await self._process_post(processor, account, post)
                    if ok:
                        result.collected += 1
                    else:
                        result.failed += 1
                        result.errors.append(f"{account.label}: {post.url[-24:]}")
        finally:
            try:
                await openai_client.close()
            except Exception:
                pass

        logger.info(
            f"Сбор завершён | новых: {result.collected} | пропущено: {result.skipped} "
            f"| ошибок: {result.failed} | {result.duration:.0f}s"
        )
        return result

    async def _process_post(
        self, processor: VideoProcessor, account: Account, post: PostRef
    ) -> bool:
        """Run the full pipeline for one post and store the outcome."""
        temp_files = []
        try:
            info = await asyncio.to_thread(get_video_info, post.url)
            metadata = collect_metadata(info)

            text_content = None
            segments = None

            try:
                text_content, subtitle_files = await processor.extract_subtitles(post.url)
                temp_files.extend(subtitle_files)
            except Exception as e:
                logger.warning(f"Субтитры недоступны: {e}")

            if not text_content:
                try:
                    text_content, segments, audio_files = await processor.extract_audio_transcript(
                        post.url
                    )
                    temp_files.extend(audio_files)
                except Exception as e:
                    logger.warning(f"Расшифровка не удалась: {e}")

            images, visual_files = await processor.collect_visual_context(post.url, info)
            temp_files.extend(visual_files)

            has_text = bool(text_content and len(text_content.strip()) >= 10)
            if not has_text and not images:
                self.storage.save_post(
                    url=post.url, platform=account.platform, account=account.handle,
                    metadata=metadata, status="empty",
                    error="ни речи, ни кадров",
                )
                return False

            analysis, analysis_path = await processor.analyze_content(
                text_content or "",
                segments,
                platform=account.platform,
                metadata=metadata,
                images=images,
            )
            if analysis_path:
                temp_files.append(analysis_path)

            self.storage.save_post(
                url=post.url,
                platform=account.platform,
                account=account.handle,
                metadata=metadata,
                transcript=(text_content or "").strip(),
                analysis=(analysis or "").strip(),
                frames=len(images),
            )
            logger.info(f"Собрано: {account.label} | {post.url[-24:]}")
            return True

        except Exception as e:
            logger.error(f"Ошибка обработки {post.url[-24:]}: {e}")
            self.storage.save_post(
                url=post.url, platform=account.platform, account=account.handle,
                status="error", error=str(e)[:500],
            )
            return False
        finally:
            cleanup_temp_files(*temp_files)


async def scheduled_scans(notify: ProgressCallback = None) -> None:
    """Background loop that scans the tracked accounts on a schedule."""
    interval_hours = settings.source_scan_interval_hours
    if interval_hours <= 0 or not settings.accounts:
        logger.info("Плановый сбор выключен")
        return

    logger.info(f"Плановый сбор включён: каждые {interval_hours} ч")
    collector = Collector()

    while True:
        try:
            result = await collector.scan()
            if notify and result.collected:
                await notify(f"🗂 Плановый сбор\n\n{result.summary()}")
        except asyncio.CancelledError:
            logger.info("Плановый сбор остановлен")
            raise
        except Exception as e:
            logger.error(f"Плановый сбор упал: {e}")

        await asyncio.sleep(interval_hours * 3600)
