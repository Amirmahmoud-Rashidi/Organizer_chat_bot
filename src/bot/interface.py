# filepath: src/bot/interface.py
"""
Build and configure the python-telegram-bot Application.

The Application is wired with all the handlers and pre-loads the
ReadOnlyClient + AIAnalyzer into `bot_data` so handlers can fetch them.
"""

from __future__ import annotations

import logging

from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.ai.analyzer import AIAnalyzer
from src.bot.handlers import cmd_lang, cmd_start, on_callback, on_text
from src.config import get_settings
from src.userbot.client import create_raw_client
from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)


def build_application(userbot: ReadOnlyClient, analyzer: AIAnalyzer) -> Application:
    """Construct the PTB Application, wiring shared objects into bot_data."""
    settings = get_settings()
    app = ApplicationBuilder().token(settings.bot_token).build()

    app.bot_data["userbot"] = userbot
    app.bot_data["analyzer"] = analyzer

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CallbackQueryHandler(on_callback))
    # Free text — everything else.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    log.info("Telegram bot application built")
    return app


def make_userbot() -> ReadOnlyClient:
    """Helper used by main.py — builds the raw client, wraps it."""
    return ReadOnlyClient(create_raw_client())