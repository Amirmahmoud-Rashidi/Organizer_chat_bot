# filepath: src/main.py
"""
Application entry point.

Flow:
    1. Load settings (validates `.env`).
    2. Configure logging.
    3. Build the read-only Telethon userbot.
    4. Build the AI analyzer (auto-detect provider).
    5. Build the BotFather bot application.
    6. Connect the userbot and start polling on the bot application.

The userbot and the bot are kept as separate connections on purpose — we
do NOT use the userbot's `TelegramClient.on(events.NewMessage(...))` for
incoming messages (we don't have an incoming-message feature; this bot
is pull-based via the /run command).
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket
import sys

from src import __version__
from src.ai.analyzer import build_analyzer
from src.bot.interface import build_application
from src.config import get_settings
from src.userbot.client import create_raw_client
from src.userbot.wrapper import ReadOnlyClient
from src.utils.logging import setup_logging

log = logging.getLogger(__name__)


# Ports we probe to detect a local HTTP proxy like Chrome-Tunnel.
# These are checked ONCE at startup; if any responds, we route HTTPS
# traffic through it. If none responds, we use the system's default
# networking (or whatever HTTPS_PROXY is already set in the environment).
_PROXY_PROBES: list[tuple[str, int, str]] = [
    ("127.0.0.1", 8765, "Chrome-Tunnel (default)"),
    ("127.0.0.1", 8080, "Common HTTP proxy"),
    ("127.0.0.1", 8888, "Common HTTP proxy"),
]


def setup_https_proxy() -> None:
    """
    Auto-detect a local HTTP proxy (Chrome-Tunnel or similar) and route
    HTTPS traffic through it.

    This affects:
      * python-telegram-bot (BotFather)
      * openai SDK (OpenRouter)
      * google-genai SDK (Google AI Studio)

    It does NOT affect Telethon — Telethon uses raw TCP+MTProto and must
    be configured separately via TELEGRAM_PROXY_* in `.env`.

    If HTTPS_PROXY is already set in the environment, we leave it alone.
    """
    # Respect explicit env first
    if os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"):
        log.info("HTTPS proxy already set in env: %s",
                 os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"))
        return

    # Check whether any session has already set it (idempotent)
    if os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"):
        return

    for host, port, label in _PROXY_PROBES:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                proxy_url = f"http://{host}:{port}"
                os.environ["HTTP_PROXY"] = proxy_url
                os.environ["HTTPS_PROXY"] = proxy_url
                log.info("Detected local proxy: %s @ %s — routing HTTPS through it",
                         label, proxy_url)
                return
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue

    log.info("No local HTTP proxy detected — HTTPS traffic will use system default")


async def run() -> None:
    settings = get_settings()
    setup_logging()
    log.info("Organizer Chat Bot v%s starting up", __version__)
    log.info(
        "Config: ai=%s/%s | allowed_user_id=%d | lang_default=%s | proxy=%s",
        settings.ai_provider,
        settings.ai_model,
        settings.allowed_user_id,
        settings.default_language,
        "ON" if settings.telegram_proxy_enabled else "off",
    )

    # Auto-detect Chrome-Tunnel for HTTPS SDKs (BotFather, AI).
    # Only takes effect if the user has Chrome-Tunnel (or similar) running.
    setup_https_proxy()

    # --- Build Telethon userbot (raw → wrapped) ---
    raw = create_raw_client()
    userbot = ReadOnlyClient(raw)

    # --- Build AI analyzer (provider auto-detected in build_analyzer) ---
    analyzer = build_analyzer()

    # --- Build PTB application ---
    app = build_application(userbot=userbot, analyzer=analyzer)

    # --- Connect userbot via the read-only wrapper ---
    log.info("Connecting Telethon userbot...")
    await userbot.start()
    me = await userbot.get_me()
    log.info("Userbot logged in as %s (id=%s)", getattr(me, "first_name", "?"), me.id)

    # --- Run bot polling until SIGINT/SIGTERM ---
    stop_event = asyncio.Event()

    def _signal_handler(*_: object) -> None:
        log.info("Shutdown signal received")
        stop_event.set()

    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _signal_handler)
    else:
        # On Windows, signal handlers in ProactorEventLoop are limited.
        signal.signal(signal.SIGINT, _signal_handler)

    async with app:
        await app.start()
        log.info("Bot is running. Press Ctrl+C to stop.")
        await app.updater.start_polling()  # type: ignore[union-attr]
        try:
            await stop_event.wait()
        finally:
            log.info("Stopping updater...")
            await app.updater.stop()  # type: ignore[union-attr]
            await app.stop()
            await userbot.disconnect()
            log.info("Clean shutdown complete")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("Interrupted")
    except Exception as exc:
        log.exception("Fatal error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()