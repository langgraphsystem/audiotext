"""
Speech-to-Text engine backed by the OpenAI Audio API.

Long recordings are transcoded and split into chunks so that videos of any
length can be transcribed: each chunk is sent separately and the resulting
segments are shifted back onto the original timeline.
"""
import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .audio import AudioChunk, prepare_for_stt
from .config import settings
from .logger import get_logger
from .stt_openai_api import transcribe_audio_file
from .utils import cleanup_temp_files

logger = get_logger(__name__)

ProgressCallback = Optional[Callable[[int, int], Awaitable[None]]]


@dataclass
class Segment:
    """Transcription segment with timestamp."""
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    """Complete transcript with segments."""
    text: str
    segments: List[Segment]
    language: Optional[str] = None


class STTEngine:
    """Speech-to-Text engine backed by the OpenAI Audio API."""

    def __init__(self):
        logger.info(f"STT engine initialized: OpenAI Audio API ({settings.stt_model})")

    async def transcribe(self, audio_path: Path, progress: ProgressCallback = None) -> Transcript:
        """Transcribe an audio or video file to text.

        Args:
            audio_path: Local media file.
            progress: Optional async callback invoked as (chunk_index, total).
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start_time = time.time()
        logger.info(f"Starting transcription of {audio_path.name}")

        chunks = await asyncio.to_thread(prepare_for_stt, audio_path)
        derived = [c.path for c in chunks if c.path != audio_path]

        try:
            return await self._transcribe_chunks(chunks, progress)
        finally:
            cleanup_temp_files(*derived)
            elapsed = time.time() - start_time
            logger.info(f"Transcription completed in {elapsed:.2f}s")

    async def _transcribe_chunks(
        self, chunks: List[AudioChunk], progress: ProgressCallback
    ) -> Transcript:
        """Transcribe every chunk and merge the results into one transcript."""
        texts: List[str] = []
        segments: List[Segment] = []
        language: Optional[str] = None
        total = len(chunks)

        if total > 1:
            logger.info(f"Transcribing {total} chunks sequentially")

        for index, chunk in enumerate(chunks, start=1):
            if progress:
                try:
                    await progress(index, total)
                except Exception as e:
                    logger.debug(f"Progress callback failed: {e}")

            result: Dict[str, Any] = await transcribe_audio_file(
                chunk.path,
                language=settings.stt_language,
            )

            chunk_text = (result.get("text") or "").strip()
            if chunk_text:
                texts.append(chunk_text)

            language = language or result.get("language")

            for raw in result.get("segments") or []:
                segments.append(Segment(
                    start=float(raw.get("start", 0.0)) + chunk.offset,
                    end=float(raw.get("end", 0.0)) + chunk.offset,
                    text=(raw.get("text") or "").strip(),
                ))

        return Transcript(text="\n".join(texts).strip(), segments=segments, language=language)

    def get_timestamped_highlights(
        self, transcript: Transcript, num_highlights: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract evenly distributed timestamped highlights from a transcript."""
        if not transcript.segments:
            return []

        total_segments = len(transcript.segments)
        step = max(1, total_segments // num_highlights)

        highlights = []
        for i in range(0, min(total_segments, num_highlights * step), step):
            segment = transcript.segments[i]
            highlights.append({
                'timestamp': format_timestamp_range(segment.start, segment.end),
                'text': segment.text,
                'start': segment.start,
                'end': segment.end,
            })

        return highlights[:num_highlights]


def format_timestamp(seconds: float) -> str:
    """Format seconds as mm:ss (or hh:mm:ss for long recordings)."""
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_timestamp_range(start: float, end: float) -> str:
    """Format a segment range as 'mm:ss - mm:ss'."""
    return f"{format_timestamp(start)} - {format_timestamp(end)}"
