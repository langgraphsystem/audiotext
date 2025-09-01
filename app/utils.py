"""
Utility functions for file operations, subtitle conversion, and text sanitization.
"""
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


def is_tiktok_url(url: str) -> bool:
    """Check if URL is a valid TikTok URL."""
    try:
        parsed = urlparse(url)
        return any(domain in parsed.netloc.lower() 
                  for domain in ['tiktok.com', 'vt.tiktok.com'])
    except Exception:
        return False


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


def get_video_info(url: str) -> Optional[dict]:
    """Get video information using yt-dlp."""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Добавляем настройки для обхода блокировок
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
            
    except Exception as e:
        logger.error(f"Error extracting video info: {e}")
        return None

