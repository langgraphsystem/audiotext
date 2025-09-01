"""
Video processing logic separated from handlers.
"""
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from .utils import vtt_or_srt_to_txt, check_file_size, cleanup_temp_files
from .yt_dlp_client import YtDlpClient
from .stt_engine import STTEngine
from .openai_client import OpenAIClient
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class VideoProcessor:
    """Handles TikTok video processing logic."""
    
    def __init__(self, yt_client: YtDlpClient, stt_engine: STTEngine, openai_client: OpenAIClient):
        self.yt_client = yt_client
        self.stt_engine = stt_engine
        self.openai_client = openai_client
    
    async def extract_subtitles(self, url: str) -> Tuple[Optional[str], List[Path]]:
        """Extract subtitles from video."""
        temp_files = []
        
        subtitle_path = await asyncio.to_thread(self.yt_client.download_subtitles, url)
        
        if subtitle_path:
            # Convert subtitle to text
            txt_path = await asyncio.to_thread(vtt_or_srt_to_txt, subtitle_path)
            temp_files.extend([subtitle_path, txt_path])
            
            with open(txt_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            return text_content, temp_files
        
        return None, temp_files
    
    async def extract_audio_transcript(self, url: str) -> Tuple[Optional[str], Optional[List], List[Path]]:
        """Extract audio and transcribe it."""
        temp_files = []
        
        # Download audio
        audio_path = await asyncio.to_thread(self.yt_client.download_audio, url)
        
        if not audio_path:
            return None, None, temp_files
        
        # Check file size
        if not check_file_size(audio_path):
            cleanup_temp_files(audio_path)
            raise ValueError(f"Файл слишком большой. Максимальный размер: {settings.max_file_size_mb} МБ.")
        
        temp_files.append(audio_path)
        
        # Transcribe audio
        transcript = await asyncio.to_thread(self.stt_engine.transcribe, audio_path)
        text_content = transcript.text
        segments = transcript.segments
        
        # Save transcript to file
        txt_path = audio_path.with_suffix('.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        temp_files.append(txt_path)
        
        return text_content, segments, temp_files
    
    async def analyze_content(self, text_content: str, segments: Optional[List] = None) -> Tuple[str, Optional[Path]]:
        """Analyze content using GPT and save to file.

        Returns a tuple of (analysis_text, analysis_path). If the analysis
        text is empty, analysis_path will be None and no file will be created.
        """
        from .config import settings
        import time
        
        # Prepare segments for analysis
        analysis_segments = None
        if segments:
            analysis_segments = [
                {
                    'timestamp': f"{seg.start:.1f}s - {seg.end:.1f}s",
                    'text': seg.text
                }
                for seg in segments
            ]
        
        # Get analysis from GPT-5
        analysis = await self.openai_client.analyze_text(text_content, analysis_segments)

        # Do not create a file when analysis is empty or whitespace-only
        if not analysis or not analysis.strip():
            logger.warning("Analysis content is empty; skipping file creation")
            return analysis, None
        
        # Save analysis to file with GPT-5 branding
        timestamp = int(time.time())
        analysis_filename = f"GPT5_TikTok_Analysis_{timestamp}.txt"
        analysis_path = settings.workdir / analysis_filename
        
        # Add header to analysis file
        header = f"""═══════════════════════════════════════════════════════════════
🧠 ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗ TIKTOK КОНТЕНТА
Powered by GPT-5 | Content Intelligence Platform
═══════════════════════════════════════════════════════════════
Дата анализа: {time.strftime('%Y-%m-%d %H:%M:%S')}
Модель: GPT-5 (Next-Generation AI)
═══════════════════════════════════════════════════════════════

"""
        
        # Use CRLF newlines for better compatibility on Windows viewers
        with open(analysis_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(header + analysis)

        return analysis, analysis_path
    
    def send_analysis_chunks(self, analysis: str) -> List[str]:
        """Split analysis into chunks for sending."""
        if not analysis or not analysis.strip():
            return []
        
        max_len = settings.max_message_length
        text = analysis.strip()
        chunks = []
        
        while text:
            chunk = text[:max_len]
            chunks.append(chunk)
            text = text[max_len:]
        
        return chunks
