# filepath: src/config.py
"""
Centralized configuration loaded from environment variables (via `.env`).

Uses pydantic-settings for type-safe validation. The bot refuses to start
if critical values are missing or inconsistent.

IMPORTANT: This module is the single source of truth for config — do NOT
read os.environ directly elsewhere.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Telegram userbot credentials ---
    telegram_api_id: int = Field(..., description="From https://my.telegram.org/apps")
    telegram_api_hash: str = Field(..., description="From https://my.telegram.org/apps")
    telegram_session_name: str = Field(
        default="organizer_userbot",
        description="File name for the persisted Telethon session.",
    )

    # --- BotFather token (for the interface bot) ---
    bot_token: str = Field(..., description="BotFather token")

    # --- Authorization ---
    allowed_user_id: int = Field(..., description="Only this Telegram user ID can use the bot")

    # --- Forwarding destination (default; can be overridden per-run via the bot UI) ---
    forward_destination: str = Field(..., description="@channel_username or numeric chat id")

    # --- AI Provider — exactly ONE of the two keys below must be set ---
    openrouter_api_key: str | None = Field(default=None)
    openrouter_model: str = Field(default="google/gemini-2.0-flash")

    google_ai_api_key: str | None = Field(default=None)
    google_ai_model: str = Field(default="gemini-2.0-flash")

    # --- Optional settings ---
    default_language: Literal["fa", "en"] = Field(default="fa")
    max_messages_per_run: int = Field(default=1000, ge=1, le=10000)
    prompt_history_limit: int = Field(default=10, ge=1, le=50)

    # --- Read pacing (anti-FloodWait / anti-ban) ---
    # Slow-read mode makes the bot's request pattern look like a human.
    # Defaults: 10 msgs/sec, with a 5s pause every 50 messages.
    slow_read_enabled: bool = Field(default=True)
    fast_batch_size: int = Field(default=10, ge=1, le=100)
    fast_batch_delay: float = Field(default=1.0, ge=0.0, le=60.0)
    batch_size: int = Field(default=50, ge=1, le=500)
    long_pause_delay: float = Field(default=5.0, ge=0.0, le=120.0)

    # --- Telethon userbot proxy (for restricted networks) ---
    # If enabled, the Telethon client connects to Telegram through this proxy.
    # Use SOCKS5 (recommended) or HTTP. The HTTPS SDKs (BotFather, OpenRouter,
    # Google AI) honor the standard HTTPS_PROXY / HTTP_PROXY env vars instead,
    # and main.py auto-detects Chrome-Tunnel at 127.0.0.1:8765.
    #
    # IMPORTANT: this is OFF by default. Only enable if you actually need it.
    # All other users will not be affected.
    telegram_proxy_enabled: bool = Field(default=False)
    telegram_proxy_type: Literal["socks5", "http"] = Field(default="socks5")
    telegram_proxy_host: str | None = Field(default=None)
    telegram_proxy_port: int | None = Field(default=None)
    telegram_proxy_username: str | None = Field(default=None)
    telegram_proxy_password: str | None = Field(default=None)
    telegram_proxy_rdns: bool = Field(default=True)

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------

    @field_validator("telegram_api_id")
    @classmethod
    def _positive_api_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("TELEGRAM_API_ID must be a positive integer")
        return v

    @field_validator("allowed_user_id")
    @classmethod
    def _positive_user_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ALLOWED_USER_ID must be a positive integer")
        return v

    @model_validator(mode="after")
    def _exactly_one_ai_provider(self) -> "Settings":
        has_openrouter = bool(self.openrouter_api_key and self.openrouter_api_key.strip())
        has_google = bool(self.google_ai_api_key and self.google_ai_api_key.strip())

        if has_openrouter and has_google:
            raise ValueError(
                "Both OPENROUTER_API_KEY and GOOGLE_AI_API_KEY are set. "
                "Please provide EXACTLY ONE AI provider key."
            )
        if not has_openrouter and not has_google:
            raise ValueError(
                "No AI provider configured. Set either OPENROUTER_API_KEY "
                "or GOOGLE_AI_API_KEY in your `.env`."
            )
        return self

    @model_validator(mode="after")
    def _validate_proxy(self) -> "Settings":
        if not self.telegram_proxy_enabled:
            return self
        if not self.telegram_proxy_host or not self.telegram_proxy_port:
            raise ValueError(
                "TELEGRAM_PROXY_ENABLED=true requires "
                "TELEGRAM_PROXY_HOST and TELEGRAM_PROXY_PORT."
            )
        if not (1 <= self.telegram_proxy_port <= 65535):
            raise ValueError("TELEGRAM_PROXY_PORT must be 1..65535")
        return self

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def ai_provider(self) -> Literal["openrouter", "google"]:
        if self.openrouter_api_key:
            return "openrouter"
        return "google"

    @property
    def ai_model(self) -> str:
        return self.openrouter_model if self.ai_provider == "openrouter" else self.google_ai_model


# Module-level singleton (lazy-initialized)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings