# filepath: src/bot/auth.py
"""
Authorization gate.

Every handler that talks to an authorized user must be wrapped with the
`authorized` decorator (or call `is_authorized` directly). Unauthorized
users get a silent ignore + a single log line; we don't want to leak
information about whether the bot is alive to unknown IDs.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from src.config import get_settings
from src.bot.i18n import Lang, t

log = logging.getLogger(__name__)


def is_authorized(user_id: int) -> bool:
    return user_id == get_settings().allowed_user_id


def authorized(
    handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]:
    """Decorator that drops any update from a non-allowed user."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        if user is None or not is_authorized(user.id):
            uid = user.id if user else "?"
            log.warning("Rejected update from unauthorized user id=%s", uid)
            # Silent ignore: do not even acknowledge. This prevents probing.
            return None
        return await handler(update, context)

    return wrapper


async def reply_auth_denied(update: Update, lang: Lang = "fa") -> None:
    """Optional explicit denial reply (used by `/start` to show a friendly message)."""
    if update.effective_message:
        await update.effective_message.reply_text(t("auth.denied", lang))