"""
Configuration management (Pydantic v2 settings).
"""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram Bot
    bot_token: str = Field(..., env="BOT_TOKEN")

    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-5", env="OPENAI_MODEL")
    # Accept Responses API token limit env to avoid validation errors
    openai_max_output_tokens: Optional[int] = Field(None, env="OPENAI_MAX_OUTPUT_TOKENS")
    openai_max_tokens: int = Field(8000, env="OPENAI_MAX_TOKENS")

    # Speech-to-Text (OpenAI Whisper API only)
    stt_language: str = Field("auto", env="STT_LANGUAGE")  # auto/en/ru/...

    # System
    workdir: Path = Field(Path("./data"), env="WORKDIR")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Rate limiting
    max_requests_per_minute: int = Field(5, env="MAX_REQUESTS_PER_MINUTE")
    max_requests_per_hour: int = Field(20, env="MAX_REQUESTS_PER_HOUR")
    
    # File processing limits
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    max_audio_duration_minutes: int = Field(10, env="MAX_AUDIO_DURATION_MINUTES")
    
    # Message limits
    max_message_length: int = Field(4000, env="MAX_MESSAGE_LENGTH")

    # Webhook (optional; use polling by default)
    webhook_base_url: Optional[str] = Field(None, env="WEBHOOK_BASE_URL")
    webhook_path: str = Field("/webhook", env="WEBHOOK_PATH")
    webhook_host: str = Field("0.0.0.0", env="WEBHOOK_HOST")
    webhook_port: int = Field(8000, env="PORT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context):
        # Ensure workdir exists
        self.workdir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
