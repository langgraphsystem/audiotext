"""
Context manager for proper resource cleanup.
"""
from contextlib import asynccontextmanager
from typing import Optional
from .yt_dlp_client import YtDlpClient
from .stt_engine import STTEngine
from .openai_client import OpenAIClient
from .utils import cleanup_temp_files
from .logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def processing_context():
    """Context manager for TikTok video processing with proper cleanup."""
    yt_client = None
    stt_engine = None
    openai_client = None
    temp_files = []
    
    try:
        # Initialize clients
        yt_client = YtDlpClient()
        stt_engine = STTEngine()
        openai_client = OpenAIClient()
        
        yield yt_client, stt_engine, openai_client, temp_files
        
    except Exception as e:
        logger.error(f"Error in processing context: {e}")
        raise
    finally:
        # Cleanup resources
        try:
            if temp_files:
                cleanup_temp_files(*temp_files)
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
        
        try:
            if openai_client:
                await openai_client.close()
        except Exception as e:
            logger.error(f"Error closing OpenAI client: {e}")