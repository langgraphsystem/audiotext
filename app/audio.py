"""
FFmpeg-based audio preparation: transcoding, probing and chunking.

The OpenAI audio endpoint accepts files up to 25 MB, so long videos are
first transcoded to a compact mono MP3 and, when still too large, split
into sequential chunks that are transcribed one by one.
"""
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

# Extensions accepted by the OpenAI audio endpoint.
SUPPORTED_UPLOAD_EXTENSIONS = {
    ".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".oga", ".ogg", ".wav", ".webm"
}


@dataclass
class AudioChunk:
    """A piece of audio and its offset (seconds) inside the original file."""
    path: Path
    offset: float


class FFmpegNotAvailable(RuntimeError):
    """Raised when FFmpeg is required but not installed."""


class NoAudioStream(RuntimeError):
    """Raised when a media file carries no audio track at all."""


def ffmpeg_path() -> Optional[str]:
    """Return the ffmpeg executable path, or None if it is not installed."""
    return shutil.which("ffmpeg")


def ffprobe_path() -> Optional[str]:
    """Return the ffprobe executable path, or None if it is not installed."""
    return shutil.which("ffprobe")


def require_ffmpeg() -> str:
    """Return the ffmpeg path or raise a descriptive error."""
    path = ffmpeg_path()
    if not path:
        raise FFmpegNotAvailable(
            "FFmpeg не найден. Установите ffmpeg, чтобы обрабатывать длинные видео."
        )
    return path


def file_size_mb(path: Path) -> float:
    """Return file size in megabytes."""
    return path.stat().st_size / (1024 * 1024) if path.exists() else 0.0


def probe_duration(path: Path) -> Optional[float]:
    """Return media duration in seconds using ffprobe, or None if unknown."""
    probe = ffprobe_path()
    if not probe or not path.exists():
        return None

    try:
        result = subprocess.run(
            [
                probe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        duration = json.loads(result.stdout).get("format", {}).get("duration")
        return float(duration) if duration is not None else None
    except Exception as e:
        logger.warning(f"ffprobe failed for {path.name}: {e}")
        return None


def has_audio_stream(path: Path) -> Optional[bool]:
    """Whether the file contains an audio track (None if ffprobe is missing)."""
    probe = ffprobe_path()
    if not probe or not path.exists():
        return None

    try:
        result = subprocess.run(
            [
                probe, "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        streams = json.loads(result.stdout).get("streams", [])
        return len(streams) > 0
    except Exception as e:
        logger.warning(f"ffprobe не смог проверить аудиодорожку {path.name}: {e}")
        return None


def extract_audio(source: Path, target: Optional[Path] = None) -> Path:
    """Transcode any media file into a compact mono MP3 suitable for STT.

    Video streams are dropped, which is what makes large videos processable:
    an hour of speech fits well under the upload limit at the default bitrate.
    """
    ffmpeg = require_ffmpeg()

    if has_audio_stream(source) is False:
        raise NoAudioStream(f"В файле {source.name} нет аудиодорожки")

    if target is None:
        target = source.with_name(f"{source.stem}_audio.mp3")
    if target.exists():
        target.unlink()

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(source),
        "-vn",
        "-ac", "1",
        "-ar", str(settings.audio_sample_rate),
        "-b:a", settings.audio_bitrate,
        str(target),
    ]

    logger.info(f"Extracting audio: {source.name} -> {target.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not target.exists():
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr.strip()[:500]}")

    logger.info(f"Audio ready: {target.name} ({file_size_mb(target):.1f} MB)")
    return target


def split_audio(source: Path, chunk_seconds: Optional[int] = None) -> List[AudioChunk]:
    """Split an audio file into sequential chunks of roughly equal length."""
    ffmpeg = require_ffmpeg()
    chunk_seconds = chunk_seconds or settings.audio_chunk_seconds

    duration = probe_duration(source)
    if duration is None:
        # Without a duration we cannot compute offsets; fall back to size-based
        # splitting where each chunk keeps the requested wall-clock length.
        logger.warning("Unknown duration, splitting blindly by segment time")

    pattern = source.with_name(f"{source.stem}_part%03d{source.suffix}")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(source),
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-c", "copy",
        str(pattern),
    ]

    logger.info(f"Splitting {source.name} into {chunk_seconds}s chunks")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg split failed: {result.stderr.strip()[:500]}")

    parts = sorted(source.parent.glob(f"{source.stem}_part*{source.suffix}"))
    if not parts:
        raise RuntimeError("FFmpeg produced no chunks")

    chunks: List[AudioChunk] = []
    offset = 0.0
    for part in parts:
        chunks.append(AudioChunk(path=part, offset=offset))
        part_duration = probe_duration(part)
        offset += part_duration if part_duration is not None else float(chunk_seconds)

    logger.info(f"Created {len(chunks)} audio chunks from {source.name}")
    return chunks


def prepare_for_stt(source: Path) -> List[AudioChunk]:
    """Return chunks ready to be uploaded to the transcription API.

    Small, already-supported files are passed through untouched; everything
    else is transcoded to mono MP3 and split when it still exceeds the limit.
    """
    limit_mb = settings.max_upload_size_mb
    size_mb = file_size_mb(source)
    suffix = source.suffix.lower()

    if size_mb <= limit_mb and suffix in SUPPORTED_UPLOAD_EXTENSIONS and suffix != ".mp4":
        logger.info(f"Using {source.name} as-is ({size_mb:.1f} MB)")
        return [AudioChunk(path=source, offset=0.0)]

    if has_audio_stream(source) is False:
        raise NoAudioStream(f"В файле {source.name} нет аудиодорожки")

    if not ffmpeg_path():
        if size_mb <= limit_mb and suffix in SUPPORTED_UPLOAD_EXTENSIONS:
            logger.warning("FFmpeg unavailable, uploading original media file")
            return [AudioChunk(path=source, offset=0.0)]
        raise FFmpegNotAvailable(
            "FFmpeg не найден, а файл слишком большой для прямой расшифровки. "
            "Установите ffmpeg."
        )

    audio = extract_audio(source)

    if file_size_mb(audio) <= limit_mb:
        return [AudioChunk(path=audio, offset=0.0)]

    # Still above the limit: split into chunks that fit.
    duration = probe_duration(audio)
    chunk_seconds = settings.audio_chunk_seconds
    if duration:
        # Aim for chunks that stay under the size limit with some headroom.
        mb_per_second = file_size_mb(audio) / duration
        if mb_per_second > 0:
            fitting = int((limit_mb * 0.9) / mb_per_second)
            chunk_seconds = max(60, min(chunk_seconds, fitting))

    chunks = split_audio(audio, chunk_seconds)

    # The intermediate full-length file is no longer needed once split.
    try:
        audio.unlink(missing_ok=True)
    except OSError as e:
        logger.warning(f"Could not remove intermediate audio {audio.name}: {e}")

    return chunks
