"""
Speech-to-Text engine using OpenAI Whisper API only.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import time
from .config import settings
from .stt_openai_api import transcribe_with_openai_whisper_api
from .logger import get_logger

logger = get_logger(__name__)


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
    """Speech-to-Text engine backed by OpenAI Whisper API."""

    def __init__(self):
        logger.info("STT engine initialized: OpenAI Whisper API mode")
    # Local model paths were removed: API-only mode
    
    def transcribe(self, audio_path: Path) -> Transcript:
        """Transcribe audio file to text."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        start_time = time.time()
        logger.info(f"Starting transcription of {audio_path.name}")
        
        try:
            return self._transcribe_openai_api(audio_path)
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
        finally:
            elapsed = time.time() - start_time
            logger.info(f"Transcription completed in {elapsed:.2f}s")

    def _transcribe_openai_api(self, audio_path: Path) -> Transcript:
        """Transcribe using OpenAI cloud Whisper API.

        This method is synchronous to fit current call sites; it creates a fresh
        event loop because it is executed inside a thread via asyncio.to_thread.
        """
        import asyncio

        # Prepare coroutine call
        async def _run():
            return await transcribe_with_openai_whisper_api(
                audio_path,
                language=settings.stt_language,
            )

        # Run in a dedicated loop for this thread
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            res: Dict[str, Any] = loop.run_until_complete(_run())
        finally:
            asyncio.set_event_loop(None)
            loop.close()

        text = (res.get("text") or "").strip()
        segs = res.get("segments") or []

        segments: List[Segment] = []
        for s in segs:
            try:
                segments.append(
                    Segment(
                        start=float(s.get("start", 0.0)),
                        end=float(s.get("end", 0.0)),
                        text=(s.get("text", "").strip()),
                    )
                )
            except Exception:
                continue

        return Transcript(
            text=text,
            segments=segments,
            language=res.get("language")
        )

    # Removed local faster-whisper and openai-whisper paths
    
    def get_timestamped_highlights(self, transcript: Transcript, num_highlights: int = 5) -> List[Dict[str, Any]]:
        """Extract timestamped highlights from transcript."""
        if not transcript.segments:
            return []
        
        # Simple approach: take evenly distributed segments
        total_segments = len(transcript.segments)
        step = max(1, total_segments // num_highlights)
        
        highlights = []
        for i in range(0, min(total_segments, num_highlights * step), step):
            segment = transcript.segments[i]
            highlights.append({
                'timestamp': f"{segment.start:.1f}s - {segment.end:.1f}s",
                'text': segment.text,
                'start': segment.start,
                'end': segment.end
            })
        
        return highlights[:num_highlights]

