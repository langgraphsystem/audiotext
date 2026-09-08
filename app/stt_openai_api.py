"""
OpenAI speech-to-text (audio transcription) via AsyncOpenAI.

Provides a singleton client and a single async transcription function that
returns text, segments and the detected language.
"""
from pathlib import Path
from typing import Optional, Dict, Any, List

from openai import AsyncOpenAI

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


_client: Optional[AsyncOpenAI] = None

# Models that support verbose_json (and therefore timestamped segments).
_SEGMENT_CAPABLE_MODELS = {"whisper-1"}


def get_client() -> AsyncOpenAI:
    """Get or create a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        api_key, base_url = settings.stt_credentials
        kwargs = {"api_key": api_key, "timeout": 300.0}
        if base_url:
            kwargs["base_url"] = base_url
        _client = AsyncOpenAI(**kwargs)
        logger.info(
            f"Initialized STT client | endpoint: {base_url or 'api.openai.com'}"
        )
    return _client


async def close_client() -> None:
    """Close the singleton client, if it was created."""
    global _client
    if _client is not None:
        try:
            await _client.close()
        finally:
            _client = None


def _normalize_segments(raw_segments) -> List[Dict[str, Any]]:
    """Convert API segments into plain dicts with float timings."""
    segments: List[Dict[str, Any]] = []
    for s in raw_segments or []:
        try:
            start = getattr(s, "start", None) if hasattr(s, "start") else s.get("start")
            end = getattr(s, "end", None) if hasattr(s, "end") else s.get("end")
            text = getattr(s, "text", None) if hasattr(s, "text") else s.get("text", "")
            segments.append({
                "start": float(start) if isinstance(start, (int, float)) else 0.0,
                "end": float(end) if isinstance(end, (int, float)) else 0.0,
                "text": (text or "").strip(),
            })
        except Exception:
            continue
    return segments


async def transcribe_audio_file(
    audio_path: Path,
    *,
    language: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """Transcribe a single audio file with the OpenAI Audio API.

    Args:
        audio_path: Local audio file (must be within the API upload limit).
        language: ISO language code, or None/"auto" for auto-detection.
        model: Transcription model; defaults to the configured STT model.
        temperature: Sampling temperature.

    Returns:
        Dict with "text" (str), "segments" (list[dict]) and "language" (str|None).
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    client = get_client()
    use_model = model or settings.stt_model or "whisper-1"
    lang_arg = None if not language or language.lower() == "auto" else language
    response_format = "verbose_json" if use_model in _SEGMENT_CAPABLE_MODELS else "json"

    logger.info(
        f"Submitting audio to OpenAI STT | file={audio_path.name} | "
        f"model={use_model} | lang={lang_arg or 'auto'}"
    )

    kwargs: Dict[str, Any] = {
        "model": use_model,
        "response_format": response_format,
        "language": lang_arg,
    }
    if response_format == "verbose_json":
        kwargs["temperature"] = temperature

    try:
        with open(audio_path, "rb") as f:
            resp = await client.audio.transcriptions.create(file=f, **kwargs)
    except Exception as e:
        logger.error(f"OpenAI STT API error: {e}")
        raise

    text = (getattr(resp, "text", "") or "").strip()
    segments = _normalize_segments(getattr(resp, "segments", None))
    language_val = getattr(resp, "language", None)

    logger.info(
        f"OpenAI STT done | chars={len(text)} | segments={len(segments)} | "
        f"lang={language_val or 'n/a'}"
    )

    return {"text": text, "segments": segments, "language": language_val}
