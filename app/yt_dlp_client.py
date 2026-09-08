"""
yt-dlp client for downloading subtitles and audio from TikTok and Instagram.
"""
import yt_dlp
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .config import settings
from .utils import safe_filename, get_video_info, base_ydl_opts, detect_platform
from .audio import extract_audio, ffmpeg_path
from .logger import get_logger

logger = get_logger(__name__)

# Media containers yt-dlp may leave on disk after a download.
MEDIA_EXTENSIONS = ('mp3', 'm4a', 'opus', 'ogg', 'webm', 'wav', 'mp4', 'mkv', 'mov')


@dataclass
class SubtitleInfo:
    """Subtitle information."""
    lang: str
    ext: str
    url: Optional[str] = None
    data: Optional[str] = None


class YtDlpClient:
    """Client for downloading content using yt-dlp."""

    def __init__(self):
        self.workdir = settings.workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        self._stem_cache = {}

    def _stem(self, url: str) -> str:
        """Build a stable, filesystem-safe stem for downloaded files."""
        if url in self._stem_cache:
            return self._stem_cache[url]

        info = get_video_info(url) or {}
        platform = detect_platform(url) or 'media'
        raw = info.get('id') or info.get('title') or 'video'
        stem = safe_filename(f"{platform}_{raw}")
        self._stem_cache[url] = stem
        return stem

    def probe_subtitles(self, url: str) -> List[SubtitleInfo]:
        """Probe available subtitles for a video URL."""
        try:
            ydl_opts = {
                **base_ydl_opts(url),
                'skip_download': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return []

            if info.get('_type') == 'playlist':
                entries = [e for e in (info.get('entries') or []) if e]
                info = entries[0] if entries else {}

            subtitles: List[SubtitleInfo] = []

            for lang, formats in (info.get('subtitles') or {}).items():
                for fmt in formats:
                    subtitles.append(SubtitleInfo(
                        lang=lang,
                        ext=fmt.get('ext', 'vtt'),
                        url=fmt.get('url'),
                        data=fmt.get('data'),
                    ))

            for lang, formats in (info.get('automatic_captions') or {}).items():
                for fmt in formats:
                    subtitles.append(SubtitleInfo(
                        lang=f"{lang}-auto",
                        ext=fmt.get('ext', 'vtt'),
                        url=fmt.get('url'),
                        data=fmt.get('data'),
                    ))

            logger.info(f"Found {len(subtitles)} subtitle formats for {url[-8:]}")
            return subtitles

        except Exception as e:
            logger.error(f"Error probing subtitles: {e}")
            return []

    def download_subtitles(self, url: str, lang_preference: List[str] = None) -> Optional[Path]:
        """Download subtitles for a video URL."""
        if lang_preference is None:
            lang_preference = ['original', 'ru', 'en', 'auto']

        try:
            available_subs = self.probe_subtitles(url)

            if not available_subs:
                logger.info("No subtitles found, will try automatic download")
                return self._download_auto_subtitles(url)

            for pref_lang in lang_preference:
                for sub in available_subs:
                    if pref_lang in sub.lang.lower():
                        return self._download_specific_subtitle(url, sub)

            if available_subs:
                return self._download_specific_subtitle(url, available_subs[0])

            return self._download_auto_subtitles(url)

        except Exception as e:
            logger.error(f"Error downloading subtitles: {e}")
            return None

    def _download_specific_subtitle(self, url: str, subtitle: SubtitleInfo) -> Optional[Path]:
        """Download a specific subtitle format."""
        try:
            stem = self._stem(url)
            desired_ext = subtitle.ext

            ydl_opts = {
                **base_ydl_opts(url),
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': False,
                'subtitleslangs': [subtitle.lang.split('-')[0]],  # Remove -auto suffix
                'subtitlesformat': desired_ext,
                # yt-dlp appends '<lang>.<ext>' to the stem
                'outtmpl': str(self.workdir / stem),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            candidates = sorted(self.workdir.glob(f"{stem}*.{desired_ext}"))
            if candidates:
                logger.info(f"Downloaded subtitle: {candidates[0].name}")
                return candidates[0]

            return None

        except Exception as e:
            logger.error(f"Error downloading specific subtitle: {e}")
            return None

    def _download_auto_subtitles(self, url: str) -> Optional[Path]:
        """Download automatic subtitles."""
        try:
            stem = self._stem(url)
            desired_ext = 'vtt'

            ydl_opts = {
                **base_ydl_opts(url),
                'skip_download': True,
                'writesubtitles': False,
                'writeautomaticsub': True,
                'subtitlesformat': desired_ext,
                'outtmpl': str(self.workdir / stem),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            candidates = sorted(self.workdir.glob(f"{stem}*.{desired_ext}"))
            if candidates:
                logger.info(f"Downloaded auto subtitle: {candidates[0].name}")
                return candidates[0]

            return None

        except Exception as e:
            logger.error(f"Error downloading auto subtitles: {e}")
            return None

    def _find_downloaded(self, stem: str) -> Optional[Path]:
        """Locate the file yt-dlp produced for a given stem."""
        for ext in MEDIA_EXTENSIONS:
            candidate = self.workdir / f"{stem}.{ext}"
            if candidate.exists():
                return candidate

        candidates = [p for p in self.workdir.glob(f"{stem}.*")
                      if p.suffix.lstrip('.').lower() in MEDIA_EXTENSIONS]
        return sorted(candidates)[0] if candidates else None

    def download_video_preview(self, url: str) -> Optional[Path]:
        """Download a low-resolution copy of the video for frame extraction.

        Video-only and capped in height, so a short clip costs a few megabytes
        and no FFmpeg merge is needed.
        """
        stem = f"{self._stem(url)}_preview"
        height = settings.vision_max_height

        opts = {
            **base_ydl_opts(url),
            'format': (
                f"bestvideo[height<={height}]/best[height<={height}]/worst"
            ),
            'outtmpl': str(self.workdir / f"{stem}.%(ext)s"),
        }

        try:
            logger.info(f"Downloading preview video for frames ({url[-12:]})")
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            logger.warning(f"Preview download failed: {e}")
            return None

        downloaded = self._find_downloaded(stem)
        if downloaded:
            logger.info(f"Preview video: {downloaded.name}")
        else:
            logger.warning("Preview download produced no file")
        return downloaded

    def download_audio(self, url: str) -> Optional[Path]:
        """Download the audio track of a TikTok or Instagram video.

        Audio-only download keeps the file small, which is what allows long
        videos to be transcribed. If the platform does not expose a separate
        audio stream, the video is downloaded and its audio extracted locally.
        """
        stem = self._stem(url)
        platform = detect_platform(url) or 'media'
        base_opts = base_ydl_opts(url)
        has_ffmpeg = ffmpeg_path() is not None

        # 1) Preferred: audio-only stream, converted to MP3 by FFmpeg.
        audio_opts = {
            **base_opts,
            'format': 'bestaudio/best',
            'outtmpl': str(self.workdir / f"{stem}.%(ext)s"),
        }
        if has_ffmpeg:
            audio_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }]
        else:
            logger.warning("FFmpeg not found: downloading audio without conversion")

        try:
            logger.info(f"Downloading audio from {platform} ({url[-12:]})")
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([url])

            downloaded = self._find_downloaded(stem)
            if downloaded:
                logger.info(f"Downloaded audio: {downloaded.name}")
                return downloaded
        except Exception as e:
            logger.warning(f"Audio-only download failed: {e}")

        # 2) Fallback: download the video and strip the audio track locally.
        video_opts = {
            **base_opts,
            # Merging separate streams needs FFmpeg; without it take a single file
            'format': 'bestvideo*+bestaudio/best' if has_ffmpeg else 'best',
            'outtmpl': str(self.workdir / f"{stem}.%(ext)s"),
        }

        try:
            logger.info("Falling back to full video download")
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                ydl.download([url])

            downloaded = self._find_downloaded(stem)
            if not downloaded:
                logger.error("Download produced no media file")
                return None

            if has_ffmpeg:
                try:
                    audio_path = extract_audio(downloaded)
                    downloaded.unlink(missing_ok=True)
                    return audio_path
                except Exception as e:
                    logger.warning(f"Local audio extraction failed: {e}")

            logger.info(f"Downloaded media: {downloaded.name}")
            return downloaded

        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
