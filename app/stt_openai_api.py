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
from .utils import is_model_unavailable_error

logger = get_logger(__name__)


_client: Optional[AsyncOpenAI] = None

# Markers of "this parameter/value is not supported by that model"
_UNSUPPORTED_PARAM_MARKERS = (
    "verbose_json",
    "timestamp_granularities",
    "response_format",
    "unsupported_value",
    "unsupported parameter",
    "unknown parameter",
    "temperature",
    "is not supported with this model",
)

# Model that worked last time, so degraded settings are not re-discovered
# on every chunk of the same file.
_working_model: Optional[str] = None


def _is_unsupported_param(error: Exception) -> bool:
    """Whether the error is about an option the model does not accept."""
    text = str(error).lower()
    return any(marker in text for marker in _UNSUPPORTED_PARAM_MARKERS)


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


def _request_variants(
    model: str, language: Optional[str], temperature: float
) -> List[Dict[str, Any]]:
    """Request options from richest to plainest.

    Timestamped segments need verbose_json; a model that rejects it still
    produces usable text through a plain json request.
    """
    variants: List[Dict[str, Any]] = []

    if settings.stt_timestamps:
        verbose: Dict[str, Any] = {
            "model": model,
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment"],
        }
        if language:
            verbose["language"] = language
        variants.append({**verbose, "temperature": temperature})
        variants.append(verbose)
        variants.append({k: v for k, v in verbose.items()
                         if k != "timestamp_granularities"})

    plain: Dict[str, Any] = {"model": model, "response_format": "json"}
    if language:
        plain["language"] = language
    variants.append(plain)
    variants.append({"model": model, "response_format": "json"})

    # Drop duplicates while preserving order
    unique: List[Dict[str, Any]] = []
    for v in variants:
        if v not in unique:
            unique.append(v)
    return unique


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

    global _working_model

    client = get_client()
    lang_arg = None if not language or language.lower() == "auto" else language

    # Configured model first, then fallbacks; stick to the one that worked
    candidates: List[str] = []
    for candidate in [model or _working_model or settings.stt_model,
                      settings.stt_model, *settings.stt_fallbacks]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    resp = None
    used_model = candidates[0]
    last_error: Optional[Exception] = None

    for use_model in candidates:
        logger.info(
            f"Submitting audio to OpenAI STT | file={audio_path.name} | "
            f"model={use_model} | lang={lang_arg or 'auto'}"
        )

        for variant in _request_variants(use_model, lang_arg, temperature):
            try:
                with open(audio_path, "rb") as f:
                    resp = await client.audio.transcriptions.create(file=f, **variant)
            except Exception as e:
                last_error = e
                if is_model_unavailable_error(e):
                    logger.warning(f"Модель распознавания {use_model} недоступна: {e}")
                    break  # try the next model
                if _is_unsupported_param(e):
                    logger.warning(
                        f"{use_model} не принял параметры "
                        f"({', '.join(k for k in variant if k != 'model')}): {e}"
                    )
                    continue  # try a simpler request
                logger.error(f"OpenAI STT API error: {e}")
                raise

            used_model = use_model
            break

        if resp is not None:
            break

    if resp is None:
        raise RuntimeError(
            f"Расшифровка не удалась ни одной из моделей: {', '.join(candidates)}"
        ) from last_error

    if used_model != _working_model:
        if _working_model is not None:
            logger.warning(f"Переключился на модель распознавания: {used_model}")
        _working_model = used_model

    text = (getattr(resp, "text", "") or "").strip()
    segments = _normalize_segments(getattr(resp, "segments", None))
    language_val = getattr(resp, "language", None)

    logger.info(
        f"OpenAI STT done | model={used_model} | chars={len(text)} | "
        f"segments={len(segments)} | lang={language_val or 'n/a'}"
    )

    return {"text": text, "segments": segments, "language": language_val}
