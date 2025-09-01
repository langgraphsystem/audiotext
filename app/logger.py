"""
Structured logging configuration.
"""
import logging
import sys
from typing import Optional
from .config import settings


def setup_logger(name: str = "tiktok_bot") -> logging.Logger:
    """Setup structured logger with proper formatting."""
    
    logger = logging.getLogger(name)
    
    if logger.handlers:  # Already configured
        return logger
    
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    # Structured format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance."""
    if name is None:
        name = "tiktok_bot"
    return setup_logger(name)


# Default logger
logger = get_logger()

