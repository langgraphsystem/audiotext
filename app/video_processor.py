"""
Video processing logic separated from handlers.
"""
import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from .config import settings
from .logger import get_logger
from .openai_client import OpenAIClient
from .stt_engine import STTEngine, format_timestamp_range
from .utils import check_file_size, cleanup_temp_files, platform_title, vtt_or_srt_to_txt
from .vision import extract_frames, frames_to_data_urls
from .yt_dlp_client import YtDlpClient

logger = get_logger(__name__)


class VideoProcessor:
    """Handles TikTok and Instagram video processing logic."""

    def __init__(self, yt_client: YtDlpClient, stt_engine: STTEngine, openai_client: OpenAIClient):
        self.yt_client = yt_client
        self.stt_engine = stt_engine
        self.openai_client = openai_client

    async def extract_subtitles(self, url: str) -> Tuple[Optional[str], List[Path]]:
        """Extract subtitles from video."""
        temp_files: List[Path] = []

        subtitle_path = await asyncio.to_thread(self.yt_client.download_subtitles, url)

        if subtitle_path:
            txt_path = await asyncio.to_thread(vtt_or_srt_to_txt, subtitle_path)
            temp_files.extend([subtitle_path, txt_path])

            with open(txt_path, 'r', encoding='utf-8') as f:
                text_content = f.read()

            if text_content.strip():
                return text_content, temp_files

        return None, temp_files

    async def extract_audio_transcript(
        self, url: str, progress=None
    ) -> Tuple[Optional[str], Optional[List], List[Path]]:
        """Download the audio track and transcribe it.

        Args:
            url: Source video URL.
            progress: Optional async callback (chunk_index, total) for long audio.
        """
        temp_files: List[Path] = []

        audio_path = await asyncio.to_thread(self.yt_client.download_audio, url)

        if not audio_path:
            return None, None, temp_files

        temp_files.append(audio_path)

        # Sanity guard against absurdly large downloads; long audio itself is
        # handled by transcoding and chunking inside the STT engine.
        if not check_file_size(audio_path):
            cleanup_temp_files(*temp_files)
            raise ValueError(
                f"Файл слишком большой. Максимальный размер: {settings.max_file_size_mb} МБ."
            )

        transcript = await self.stt_engine.transcribe(audio_path, progress=progress)
        text_content = transcript.text
        segments = transcript.segments

        if not text_content.strip():
            return None, None, temp_files

        txt_path = audio_path.with_suffix('.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        temp_files.append(txt_path)

        return text_content, segments, temp_files

    async def collect_visual_context(
        self, url: str, video_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Path]]:
        """Download a low-res copy of the video and extract key frames.

        Returns (data URLs for the model, temp files to clean up). Never
        raises: the visual pass is a bonus on top of the transcript.
        """
        if not settings.vision_enabled or settings.vision_frames <= 0:
            return [], []

        duration = (video_info or {}).get('duration') or 0
        limit_seconds = settings.vision_max_duration_minutes * 60
        if duration and duration > limit_seconds:
            logger.info(
                f"Ролик длиннее {settings.vision_max_duration_minutes} мин "
                "— кадры не извлекаю"
            )
            return [], []

        try:
            preview = await asyncio.to_thread(self.yt_client.download_video_preview, url)
            if not preview:
                return [], []

            frames = await asyncio.to_thread(extract_frames, preview)
            images = frames_to_data_urls(frames)
            return images, [preview, *frames]
        except Exception as e:
            logger.warning(f"Визуальный разбор пропущен: {e}")
            return [], []

    async def analyze_content(
        self,
        text_content: str,
        segments: Optional[List] = None,
        platform: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        images: Optional[List[str]] = None,
    ) -> Tuple[str, Optional[Path]]:
        """Analyze content with the model and save the report to a file.

        Returns a tuple of (analysis_text, analysis_path). If the analysis
        text is empty, analysis_path will be None and no file will be created.
        """
        analysis_segments: Optional[List[Dict[str, Any]]] = None
        if segments:
            analysis_segments = [
                {
                    'timestamp': format_timestamp_range(seg.start, seg.end),
                    'text': seg.text,
                }
                for seg in segments
            ]

        analysis = await self.openai_client.analyze_text(
            text_content,
            analysis_segments,
            platform=platform,
            metadata=metadata,
            images=images,
        )

        if not analysis or not analysis.strip():
            logger.warning("Analysis content is empty; skipping file creation")
            return analysis, None

        brand = settings.brand_name
        source = platform_title(platform)
        timestamp = int(time.time())
        analysis_filename = f"{brand.replace(' ', '_')}_Analysis_{timestamp}.txt"
        analysis_path = settings.workdir / analysis_filename

        visual_note = f"Кадров разобрано: {len(images)}\n" if images else ""

        header = f"""═══════════════════════════════════════════════════════════════
🌙 ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗ КОНТЕНТА · {source.upper()}
Powered by {brand} | Content Intelligence Platform
═══════════════════════════════════════════════════════════════
Дата анализа: {time.strftime('%Y-%m-%d %H:%M:%S')}
Ассистент: {brand}
Модель ИИ: {settings.model_display_name}
{visual_note}═══════════════════════════════════════════════════════════════

"""

        # Use CRLF newlines for better compatibility on Windows viewers
        with open(analysis_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(header + analysis)

        return analysis, analysis_path

    def send_analysis_chunks(self, analysis: str) -> List[str]:
        """Split analysis into chunks for sending."""
        if not analysis or not analysis.strip():
            return []

        max_len = settings.max_message_length
        text = analysis.strip()
        chunks = []

        while text:
            chunks.append(text[:max_len])
            text = text[max_len:]

        return chunks
