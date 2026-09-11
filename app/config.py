"""
Configuration management (Pydantic v2 settings).

Every field is read from the environment variable with the same name in
upper case (``bot_token`` ← ``BOT_TOKEN``). Where the deployment platform
dictates a different name, an explicit ``validation_alias`` is used.
"""
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Branding
    brand_name: str = "ChatGPT Luna"
    # Name of the AI model shown to users; the technical id stays in OPENAI_MODEL
    model_display_name: str = "Luna"

    # Telegram Bot
    bot_token: str

    # AI backend (OpenAI or any OpenAI-compatible API)
    openai_api_key: str
    openai_model: str = "gpt-5.6-luna"
    # Custom endpoint, e.g. https://api.your-provider.com/v1
    openai_base_url: Optional[str] = None
    # Comma-separated models tried, in order, if the configured one is
    # unavailable for the key (empty disables the fallback)
    openai_fallback_models: str = ""
    openai_max_output_tokens: Optional[int] = None
    openai_max_tokens: int = 8000

    # Reasoning parameters (GPT-5.6 family)
    # none/low/medium/high/xhigh/max
    openai_reasoning_effort: str = "medium"
    # standard/pro — "pro" is what GPT-5.6 Luna Pro is served with
    openai_reasoning_mode: Optional[str] = None
    openai_verbosity: str = "medium"  # low/medium/high

    # Speech-to-Text (OpenAI Audio API)
    stt_language: str = "auto"  # auto/en/ru/...
    # gpt-transcribe is OpenAI's recommended transcription model; whisper-1
    # stays available as a fallback for keys without access to it
    stt_model: str = "gpt-transcribe"
    stt_fallback_models: str = "whisper-1"
    # Ask for segment timestamps (needed for timestamped highlights)
    stt_timestamps: bool = True
    # Transcription may live on a different provider than the analysis model
    stt_api_key: Optional[str] = None
    stt_base_url: Optional[str] = None

    # Audio preparation (FFmpeg)
    audio_bitrate: str = "64k"
    audio_sample_rate: int = 16000
    # Long audio is split into chunks before transcription (seconds)
    audio_chunk_seconds: int = 600

    # Visual analysis (key frames sent to the model alongside the transcript)
    vision_enabled: bool = True
    vision_frames: int = 4
    vision_frame_width: int = 640
    # Downloading video for frames is only worth it for reasonably short clips
    vision_max_duration_minutes: int = 20
    vision_max_height: int = 480

    # Collection of tracked accounts
    # Comma-separated: full profile URLs or "tiktok:@user" / "instagram:user"
    source_accounts: str = ""
    # How often the collector walks the accounts (0 disables the schedule)
    source_scan_interval_hours: int = 24
    # New posts taken per account per scan
    source_max_items_per_account: int = 3
    # Chat that receives scan digests; also the only chat allowed to run /scan
    admin_chat_id: Optional[int] = None

    # System
    workdir: Path = Path("./data")
    # SQLite file with collected posts (put it on a volume to survive redeploys)
    database_path: Optional[Path] = None
    log_level: str = "INFO"
    # Remove leftover media from previous runs on startup (ephemeral hosts)
    clean_workdir_on_start: bool = True

    # Cookies for age/login restricted content (Instagram in particular)
    instagram_cookies_file: Optional[Path] = None
    tiktok_cookies_file: Optional[Path] = None
    # Same cookies as a base64 string, for hosts where a file cannot be mounted
    instagram_cookies_b64: Optional[str] = None
    tiktok_cookies_b64: Optional[str] = None

    # Rate limiting
    max_requests_per_minute: int = 5
    max_requests_per_hour: int = 20

    # File processing limits
    # Hard limit of the OpenAI audio endpoint is 25 MB per request; larger
    # audio is transcoded and split into chunks instead of being rejected.
    max_upload_size_mb: int = 24
    # Upper bound for a downloaded media file before we even try to process it.
    max_file_size_mb: int = 500
    max_audio_duration_minutes: int = 120

    # Message limits
    max_message_length: int = 4000

    # Webhook (optional; polling is used when no public URL is known)
    webhook_base_url: Optional[str] = None
    webhook_path: str = "/webhook"
    webhook_host: str = "0.0.0.0"
    # Shared secret Telegram sends back in X-Telegram-Bot-Api-Secret-Token
    webhook_secret: Optional[str] = None
    # Railway (and most PaaS) inject the port to bind as PORT
    webhook_port: int = Field(
        8000, validation_alias=AliasChoices("PORT", "WEBHOOK_PORT")
    )

    # Railway injects the public domain of the service; used to build the
    # webhook URL automatically when WEBHOOK_BASE_URL is not set.
    railway_public_domain: Optional[str] = Field(
        None,
        validation_alias=AliasChoices(
            "RAILWAY_PUBLIC_DOMAIN", "RAILWAY_STATIC_URL", "PUBLIC_DOMAIN"
        ),
    )
    # Explicit switch: true → webhook, false → polling. When unset, the mode
    # is decided by whether WEBHOOK_BASE_URL was provided explicitly, so a
    # platform-provided domain alone never changes the running mode.
    use_webhook: Optional[bool] = None

    _webhook_base_url_explicit: bool = PrivateAttr(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context):
        # Ensure workdir exists
        self.workdir.mkdir(parents=True, exist_ok=True)

        if self.database_path is None:
            self.database_path = self.workdir / "collected.db"

        self._webhook_base_url_explicit = bool(self.webhook_base_url)

        # Derive the webhook base URL from the platform-provided domain
        if not self.webhook_base_url and self.railway_public_domain:
            domain = self.railway_public_domain.strip().rstrip("/")
            if not domain.startswith("http"):
                domain = f"https://{domain}"
            self.webhook_base_url = domain

        if self.webhook_path and not self.webhook_path.startswith("/"):
            self.webhook_path = f"/{self.webhook_path}"

    @property
    def accounts(self) -> list[str]:
        """Tracked account specs, as written in SOURCE_ACCOUNTS."""
        return [a.strip() for a in self.source_accounts.split(",") if a.strip()]

    @property
    def fallback_models(self) -> list[str]:
        """Analysis models to try if the configured one is not available."""
        return [m.strip() for m in self.openai_fallback_models.split(",") if m.strip()]

    @property
    def stt_fallbacks(self) -> list[str]:
        """Transcription models to try if the configured one is unavailable."""
        return [m.strip() for m in self.stt_fallback_models.split(",") if m.strip()]

    @property
    def stt_credentials(self) -> tuple[str, Optional[str]]:
        """API key and base URL used for transcription."""
        return (self.stt_api_key or self.openai_api_key,
                self.stt_base_url or self.openai_base_url)

    @property
    def webhook_enabled(self) -> bool:
        """Whether the bot should run in webhook mode."""
        if self.use_webhook is not None:
            return self.use_webhook
        return self._webhook_base_url_explicit

    @property
    def webhook_url(self) -> Optional[str]:
        """Full webhook URL, if a base URL is known."""
        if not self.webhook_base_url:
            return None
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"


# Global settings instance
settings = Settings()
