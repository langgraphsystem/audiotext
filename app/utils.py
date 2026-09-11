"""
Utility functions for file operations, subtitle conversion, and text sanitization.
"""
import base64
import re
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import yt_dlp
import os
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


# Markers of "this key cannot use this model" in provider error messages
MODEL_UNAVAILABLE_MARKERS = (
    "model_not_found",
    "does not exist",
    "do not have access",
    "not have access",
    "unknown model",
    "invalid model",
    "unsupported model",
    "model is not supported",
)


def is_model_unavailable_error(error: Exception) -> bool:
    """Whether the error means the model itself is unusable for this key."""
    text = str(error).lower()
    return any(marker in text for marker in MODEL_UNAVAILABLE_MARKERS)


# Supported platforms and the domains they are recognised by.
PLATFORM_DOMAINS = {
    'tiktok': ('tiktok.com', 'vt.tiktok.com', 'vm.tiktok.com'),
    'instagram': ('instagram.com', 'instagr.am', 'ig.me'),
}

PLATFORM_TITLES = {
    'tiktok': 'TikTok',
    'instagram': 'Instagram',
}

# Matches both bare and full links of every supported platform.
SUPPORTED_URL_REGEX = (
    r"(https?://)?(www\.)?((vt\.|vm\.)?tiktok\.com|instagram\.com|instagr\.am)"
)


def detect_platform(url: str) -> Optional[str]:
    """Return the platform key for a URL ('tiktok'/'instagram'), or None."""
    try:
        candidate = url if '://' in url else f'https://{url}'
        netloc = urlparse(candidate).netloc.lower()
        if not netloc:
            return None
        for platform, domains in PLATFORM_DOMAINS.items():
            if any(netloc == d or netloc.endswith(f'.{d}') or netloc == f'www.{d}'
                   for d in domains):
                return platform
    except Exception:
        return None
    return None


def platform_title(platform: Optional[str]) -> str:
    """Human readable platform name."""
    return PLATFORM_TITLES.get(platform or '', 'видео')


def is_supported_url(url: str) -> bool:
    """Check if URL belongs to one of the supported platforms."""
    return detect_platform(url) is not None


def is_tiktok_url(url: str) -> bool:
    """Check if URL is a valid TikTok URL."""
    return detect_platform(url) == 'tiktok'


def is_instagram_url(url: str) -> bool:
    """Check if URL is a valid Instagram URL."""
    return detect_platform(url) == 'instagram'


def extract_supported_urls(text: str) -> list:
    """Extract every supported URL from a free-form message."""
    words = re.split(r'\s+', text or '')
    return [w.strip('.,;:!?()[]<>"\'') for w in words
            if is_supported_url(w.strip('.,;:!?()[]<>"\''))]


def safe_filename(title_or_id: str) -> str:
    """Create a safe filename from title or ID."""
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', title_or_id)
    # Normalize unicode
    safe = unicodedata.normalize('NFKC', safe)
    # Remove extra whitespace
    safe = re.sub(r'\s+', ' ', safe).strip()
    # Limit length
    return safe[:100] if len(safe) > 100 else safe


def strip_markup(text: str) -> str:
    """Remove HTML/XML markup from text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove XML entities
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def vtt_or_srt_to_txt(subtitle_path: Path) -> Path:
    """Convert VTT or SRT subtitle file to plain text."""
    txt_path = subtitle_path.with_suffix('.txt')
    
    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove timestamps and formatting
        if subtitle_path.suffix.lower() == '.vtt':
            # VTT format: remove WEBVTT header, timestamps, and cue identifiers
            lines = content.split('\n')
            text_lines = []
            skip_next = False
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('WEBVTT') or '-->' in line:
                    continue
                if re.match(r'^\d+$', line):  # Cue identifier
                    continue
                text_lines.append(line)
            
            text = ' '.join(text_lines)
            
        elif subtitle_path.suffix.lower() == '.srt':
            # SRT format: remove sequence numbers, timestamps, and empty lines
            lines = content.split('\n')
            text_lines = []
            skip_next = False
            
            for line in lines:
                line = line.strip()
                if not line or re.match(r'^\d+$', line) or '-->' in line:
                    continue
                text_lines.append(line)
            
            text = ' '.join(text_lines)
        
        else:
            # Assume plain text
            text = content
        
        # Clean up the text
        text = strip_markup(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Write to TXT file
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Converted {subtitle_path.name} to {txt_path.name}")
        return txt_path
        
    except Exception as e:
        logger.error(f"Error converting subtitle file: {e}")
        raise


def cleanup_temp_files(*file_paths: Path) -> None:
    """Clean up temporary files."""
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")


def check_file_size(file_path: Path) -> bool:
    """Check if file size is within limits."""
    if not file_path.exists():
        return True
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    max_size = settings.max_file_size_mb
    
    if file_size_mb > max_size:
        logger.warning(f"File {file_path.name} is too large: {file_size_mb:.1f}MB (limit: {max_size}MB)")
        return False
    
    return True


def check_audio_duration(info: dict) -> bool:
    """Check if audio duration is within limits."""
    if not info:
        return True
    
    duration = info.get('duration')
    if duration is None:
        return True
    
    duration_minutes = duration / 60
    max_duration = settings.max_audio_duration_minutes
    
    if duration_minutes > max_duration:
        logger.warning(f"Audio duration is too long: {duration_minutes:.1f}min (limit: {max_duration}min)")
        return False
    
    return True


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _cookie_file_from_b64(platform: str, encoded: str) -> Optional[Path]:
    """Write a base64-encoded cookies file to disk once and return its path.

    Kept in a subdirectory: clean_workdir() wipes *.txt at the root.
    """
    target = settings.workdir / "cookies" / f"{platform}.txt"
    if target.exists() and target.stat().st_size > 0:
        return target

    try:
        data = base64.b64decode(encoded, validate=True)
    except Exception as e:
        logger.error(f"Не удалось раскодировать cookies для {platform}: {e}")
        return None

    if not data.strip():
        return None

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o600)
        logger.info(f"Cookies для {platform} записаны из переменной окружения")
        return target
    except OSError as e:
        logger.error(f"Не удалось сохранить cookies для {platform}: {e}")
        return None


def cookie_file_for(platform: Optional[str]) -> Optional[Path]:
    """Cookies path for a platform: explicit file first, then the base64 form."""
    if platform == 'instagram':
        path, encoded = settings.instagram_cookies_file, settings.instagram_cookies_b64
    elif platform == 'tiktok':
        path, encoded = settings.tiktok_cookies_file, settings.tiktok_cookies_b64
    else:
        return None

    if path:
        cookies_path = Path(path)
        if cookies_path.exists():
            return cookies_path
        logger.warning(f"Cookies file not found: {cookies_path}")

    if encoded:
        return _cookie_file_from_b64(platform, encoded)

    return None


def base_ydl_opts(url: str) -> dict:
    """Common yt-dlp options, including per-platform cookies when configured."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': USER_AGENT},
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
        'extractor_retries': 3,
        'noplaylist': True,
    }

    platform = detect_platform(url)
    if platform == 'instagram':
        # Instagram serves the page differently to a plain UA
        opts['http_headers']['Referer'] = 'https://www.instagram.com/'

    cookies_path = cookie_file_for(platform)
    if cookies_path:
        opts['cookiefile'] = str(cookies_path)
    elif settings.cookies_from_browser:
        # Local runs can borrow the browser session directly
        browser = settings.cookies_from_browser.strip().lower()
        opts['cookiesfrombrowser'] = (browser,)
        logger.info(f"Беру cookies из браузера: {browser}")

    return opts


def collect_metadata(info: Optional[dict]) -> dict:
    """Pick the fields worth showing to the analysis model.

    Titles, descriptions, hashtags and engagement numbers say a lot about a
    clip that never appears in the spoken transcript.
    """
    if not info:
        return {}

    fields = {
        'id': info.get('id'),
        'title': info.get('title'),
        'description': info.get('description'),
        'uploader': info.get('uploader') or info.get('channel'),
        'duration': info.get('duration'),
        'view_count': info.get('view_count'),
        'like_count': info.get('like_count'),
        'comment_count': info.get('comment_count'),
        'repost_count': info.get('repost_count'),
        'upload_date': info.get('upload_date'),
        'track': info.get('track'),
        'artist': info.get('artist'),
    }

    tags = info.get('tags') or info.get('hashtags') or []
    if isinstance(tags, list) and tags:
        fields['tags'] = [str(t) for t in tags[:20]]

    return {k: v for k, v in fields.items() if v not in (None, '', [], 0)}


def get_video_info(url: str) -> Optional[dict]:
    """Get video information using yt-dlp."""
    try:
        ydl_opts = {**base_ydl_opts(url), 'extract_flat': False, 'skip_download': True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Instagram carousels return a playlist: take the first playable entry
        if info and info.get('_type') == 'playlist':
            entries = [e for e in (info.get('entries') or []) if e]
            if entries:
                logger.info(f"Playlist detected, using first of {len(entries)} entries")
                return entries[0]

        return info

    except Exception as e:
        logger.error(f"Error extracting video info: {e}")
        return None

