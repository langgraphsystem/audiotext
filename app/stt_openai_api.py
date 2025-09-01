"""
OpenAI STT (audio transcription) via AsyncOpenAI.

Provides a small wrapper with a singleton client and an async
transcription function that returns text and optional segments.
"""
from pathlib import Path
from typing import Optional, Dict, Any, List

from openai import AsyncOpenAI

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """Get or create a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=90.0)
        logger.info("Initialized OpenAI STT client (AsyncOpenAI)")
    return _client


def _client_singleton() -> AsyncOpenAI:
    """Compatibility alias for a singleton client getter."""
    return get_client()


async def transcribe_openai_api(
    audio_path: Path,
    *,
    language: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Transcribe an audio/video file using OpenAI Audio Transcriptions API.

    Args:
        audio_path: Path to local audio/video file.
        language: ISO language code (e.g. "ru"). If None, auto-detect.
        model: Transcription model. Defaults to "whisper-1" if not provided.

    Returns:
        Dict with keys: "text" (str), "segments" (list[dict]), optionally "language".
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    client = get_client()

    # Default to widely available model name
    use_model = model or "whisper-1"

    # Normalize language: None means auto-detect
    lang_arg = None if not language or language.lower() == "auto" else language

    logger.info(
        f"Submitting audio to OpenAI STT | file={audio_path.name} | model={use_model} | lang={lang_arg or 'auto'}"
    )

    # verbose_json yields segments and metadata when available
    try:
        with open(audio_path, "rb") as f:
            resp = await client.audio.transcriptions.create(
                model=use_model,
                file=f,
                response_format="verbose_json",
                language=lang_arg,
            )
    except Exception as e:
        logger.error(f"OpenAI STT API error: {e}")
        raise

    # resp is a pydantic object; access like attributes
    text: str = (getattr(resp, "text", "") or "").strip()

    raw_segments: List[Dict[str, Any]] = []
    try:
        segs = getattr(resp, "segments", None) or []
        for s in segs:
            # s can be dict-like; use getattr/get for safety
            start = getattr(s, "start", None) if hasattr(s, "start") else s.get("start")
            end = getattr(s, "end", None) if hasattr(s, "end") else s.get("end")
            seg_text = getattr(s, "text", None) if hasattr(s, "text") else s.get("text", "")
            raw_segments.append(
                {
                    "start": float(start) if isinstance(start, (int, float)) else 0.0,
                    "end": float(end) if isinstance(end, (int, float)) else 0.0,
                    "text": (seg_text or "").strip(),
                }
            )
    except Exception:
        # If segments format changes or not returned, continue with text only
        raw_segments = []

    out: Dict[str, Any] = {"text": text, "segments": raw_segments}

    # Some responses include language field
    try:
        lang_val = getattr(resp, "language", None)
        if lang_val:
            out["language"] = lang_val
    except Exception:
        pass

    logger.info(
        f"OpenAI STT done | chars={len(text)} | segments={len(raw_segments)} | lang={out.get('language', 'n/a')}"
    )

    return out


async def transcribe_with_openai_whisper_api(
    audio_path: Path,
    *,
    language: Optional[str] = None,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """Transcription via OpenAI Whisper API (cloud).

    Returns a dict with keys: "text": str, "segments": list|None, "language": str|None
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    client = _client_singleton()
    use_lang = None if not language or language == "auto" else language
    model = "whisper-1"

    logger.info(f"Sending {audio_path.name} to OpenAI Whisper API...")
    try:
        with open(audio_path, "rb") as f:
            resp = await client.audio.transcriptions.create(
                model=model,
                file=f,
                language=use_lang,
                response_format="verbose_json",
                temperature=temperature,
            )
    except Exception as e:
        logger.error(f"OpenAI Whisper API error: {e}")
        raise

    text = (getattr(resp, "text", "") or "").strip()
    segs = getattr(resp, "segments", None)
    language_val = getattr(resp, "language", None)

    # Normalize segments to list of plain dicts if available
    segments: Optional[List[Dict[str, Any]]]
    if segs:
        try:
            segments = []
            for s in segs:
                start = getattr(s, "start", None) if hasattr(s, "start") else s.get("start")
                end = getattr(s, "end", None) if hasattr(s, "end") else s.get("end")
                seg_text = getattr(s, "text", None) if hasattr(s, "text") else s.get("text", "")
                segments.append(
                    {
                        "start": float(start) if isinstance(start, (int, float)) else 0.0,
                        "end": float(end) if isinstance(end, (int, float)) else 0.0,
                        "text": (seg_text or "").strip(),
                    }
                )
        except Exception:
            segments = None
    else:
        segments = None

    logger.info(
        f"Whisper transcription done | chars={len(text)} | segments={len(segments) if segments else 0} | lang={language_val or 'n/a'}"
    )

    return {
        "text": text,
        "segments": segments,
        "language": language_val,
    }
