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
import signal
import sys

from src import __version__
from src.ai.analyzer import build_analyzer
from src.bot.interface import build_application
from src.config import get_settings
from src.userbot.client import create_raw_client
from src.userbot.wrapper import ReadOnlyClient
from src.utils.logging import setup_logging

log = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    setup_logging()
    log.info("Organizer Chat Bot v%s starting up", __version__)
    log.info(
        "Config: ai=%s/%s | allowed_user_id=%d | lang_default=%s",
        settings.ai_provider,
        settings.ai_model,
        settings.allowed_user_id,
        settings.default_language,
    )

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