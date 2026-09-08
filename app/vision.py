"""
Visual analysis helpers: key frames extracted from the video itself.

The transcript only carries what was said. Short-form video usually shows
much more — on-screen text, the product, the setting — so a few key frames
are extracted and passed to the model alongside the transcript.
"""
import base64
import subprocess
from pathlib import Path
from typing import List, Optional

from .audio import ffmpeg_path, file_size_mb, probe_duration
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

# Skip frames that would blow up the request; the API limit is per image.
MAX_FRAME_MB = 4.0


def extract_frames(video_path: Path, count: Optional[int] = None) -> List[Path]:
    """Extract evenly spaced key frames from a video file."""
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        logger.warning("FFmpeg not found: skipping frame extraction")
        return []

    count = count or settings.vision_frames
    if count <= 0 or not video_path.exists():
        return []

    duration = probe_duration(video_path)
    if duration and duration > 0:
        # Sample at the middle of each equal slice, avoiding black first frames
        timestamps = [duration * (i + 0.5) / count for i in range(count)]
    else:
        timestamps = [0.0]

    frames: List[Path] = []
    for index, timestamp in enumerate(timestamps):
        target = video_path.with_name(f"{video_path.stem}_frame{index:02d}.jpg")
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{timestamp:.2f}",
            "-i", str(video_path),
            "-frames:v", "1",
            "-vf", f"scale={settings.vision_frame_width}:-2",
            "-q:v", "4",
            str(target),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not target.exists():
            logger.warning(f"Frame at {timestamp:.1f}s failed: {result.stderr.strip()[:200]}")
            continue

        if file_size_mb(target) > MAX_FRAME_MB:
            logger.warning(f"Frame {target.name} too large, skipping")
            target.unlink(missing_ok=True)
            continue

        frames.append(target)

    logger.info(f"Extracted {len(frames)} frames from {video_path.name}")
    return frames


def frame_to_data_url(frame_path: Path) -> Optional[str]:
    """Encode a frame as a data URL for the Responses API."""
    try:
        encoded = base64.b64encode(frame_path.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        logger.warning(f"Could not encode {frame_path.name}: {e}")
        return None


def frames_to_data_urls(frames: List[Path]) -> List[str]:
    """Encode every frame, dropping the ones that fail."""
    urls = [frame_to_data_url(f) for f in frames]
    return [u for u in urls if u]
