"""
yt-dlp client for downloading subtitles and audio from TikTok videos.
"""
import yt_dlp
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .config import settings
from .utils import safe_filename, get_video_info
from .logger import get_logger

logger = get_logger(__name__)


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
    
    def probe_subtitles(self, url: str) -> List[SubtitleInfo]:
        """Probe available subtitles for a TikTok URL."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                subtitles = []
                
                # Check manual subtitles
                if 'subtitles' in info:
                    for lang, formats in info['subtitles'].items():
                        for fmt in formats:
                            subtitles.append(SubtitleInfo(
                                lang=lang,
                                ext=fmt.get('ext', 'vtt'),
                                url=fmt.get('url'),
                                data=fmt.get('data')
                            ))
                
                # Check automatic subtitles
                if 'automatic_captions' in info:
                    for lang, formats in info['automatic_captions'].items():
                        for fmt in formats:
                            subtitles.append(SubtitleInfo(
                                lang=f"{lang}-auto",
                                ext=fmt.get('ext', 'vtt'),
                                url=fmt.get('url'),
                                data=fmt.get('data')
                            ))
                
                logger.info(f"Found {len(subtitles)} subtitle formats for {url[-8:]}")
                return subtitles
                
        except Exception as e:
            logger.error(f"Error probing subtitles: {e}")
            return []
    
    def download_subtitles(self, url: str, lang_preference: List[str] = None) -> Optional[Path]:
        """Download subtitles for a TikTok URL."""
        if lang_preference is None:
            lang_preference = ['original', 'en', 'auto']
        
        try:
            # First try to get available subtitles
            available_subs = self.probe_subtitles(url)
            
            if not available_subs:
                logger.info("No subtitles found, will try automatic download")
                return self._download_auto_subtitles(url)
            
            # Try to find preferred language
            for pref_lang in lang_preference:
                for sub in available_subs:
                    if pref_lang in sub.lang.lower():
                        return self._download_specific_subtitle(url, sub)
            
            # Fallback to first available subtitle
            if available_subs:
                return self._download_specific_subtitle(url, available_subs[0])
            
            # Last resort: try automatic download
            return self._download_auto_subtitles(url)
            
        except Exception as e:
            logger.error(f"Error downloading subtitles: {e}")
            return None
    
    def _download_specific_subtitle(self, url: str, subtitle: SubtitleInfo) -> Optional[Path]:
        """Download a specific subtitle format."""
        try:
            video_info = get_video_info(url)
            if not video_info:
                return None

            title = safe_filename(video_info.get('title', 'video'))
            # We'll search for resulting subtitle by glob after download
            desired_ext = subtitle.ext

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': False,
                'subtitleslangs': [subtitle.lang.split('-')[0]],  # Remove -auto suffix
                'subtitlesformat': desired_ext,
                # Use title stem; yt-dlp will append language/ext like '<title>.<lang>.<ext>'
                'outtmpl': str(self.workdir / title),
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
                ydl.download([url])
            # Find produced subtitle file(s) like '<title>.*.<ext>'
            candidates = sorted(self.workdir.glob(f"{title}*.{desired_ext}"))
            if candidates:
                chosen = candidates[0]
                logger.info(f"Downloaded subtitle: {chosen.name}")
                return chosen

            return None
            
        except Exception as e:
            logger.error(f"Error downloading specific subtitle: {e}")
            return None
    
    def _download_auto_subtitles(self, url: str) -> Optional[Path]:
        """Download automatic subtitles."""
        try:
            video_info = get_video_info(url)
            if not video_info:
                return None

            title = safe_filename(video_info.get('title', 'video'))
            desired_ext = 'vtt'

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': False,
                'writeautomaticsub': True,
                'subtitlesformat': desired_ext,
                'outtmpl': str(self.workdir / title),
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
                ydl.download([url])
            candidates = sorted(self.workdir.glob(f"{title}*.{desired_ext}"))
            if candidates:
                chosen = candidates[0]
                logger.info(f"Downloaded auto subtitle: {chosen.name}")
                return chosen

            return None
            
        except Exception as e:
            logger.error(f"Error downloading auto subtitles: {e}")
            return None
    
    def download_audio(self, url: str) -> Optional[Path]:
        """Download best audio track from TikTok video."""
        try:
            video_info = get_video_info(url)
            if not video_info:
                return None
            
            title = safe_filename(video_info.get('title', 'video'))
            audio_path = self.workdir / f"{title}.mp3"
            
            # For TikTok, download video first (like in your working code)
            if "tiktok.com" in url:
                logger.info("TikTok detected, downloading video file...")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'mp4',
                    'outtmpl': str(audio_path.with_suffix('.mp4')),
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
                    ydl.download([url])
                
                # Check if video file was created
                video_path = audio_path.with_suffix('.mp4')
                if video_path.exists():
                    logger.info(f"Downloaded TikTok video: {video_path.name}")
                    return video_path
                
                # Try alternative video formats
                for ext in ['mp4', 'webm', 'mkv']:
                    alt_path = audio_path.with_suffix(f'.{ext}')
                    if alt_path.exists():
                        logger.info(f"Downloaded video file: {alt_path.name}")
                        return alt_path
            else:
                # For other platforms, try audio download
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'bestaudio/best[height<=720]',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': str(audio_path.with_suffix('')),
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
                    ydl.download([url])
                
                # Check if file was created
                if audio_path.exists():
                    logger.info(f"Downloaded audio: {audio_path.name}")
                    return audio_path
                
                # Try alternative extensions
                for ext in ['mp3', 'm4a', 'webm', 'ogg']:
                    alt_path = audio_path.with_suffix(f'.{ext}')
                    if alt_path.exists():
                        logger.info(f"Downloaded audio: {alt_path.name}")
                        return alt_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            # Try with a more basic format as fallback
            try:
                logger.info("Trying fallback download...")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'best',
                    'outtmpl': str(audio_path.with_suffix('')),
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
                    ydl.download([url])
                
                # Check if any file was created
                for ext in ['mp4', 'webm', 'mkv', 'mp3', 'm4a']:
                    alt_path = audio_path.with_suffix(f'.{ext}')
                    if alt_path.exists():
                        logger.info(f"Downloaded file: {alt_path.name}")
                        return alt_path
                
            except Exception as e2:
                logger.error(f"Fallback download also failed: {e2}")
            
            return None

