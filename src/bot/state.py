# filepath: src/bot/state.py
"""
In-memory per-user state.

Because the bot is single-user (hardcoded ALLOWED_USER_ID), this module just
holds a small dict keyed by the authorized user id. If we ever go multi-user,
swap the storage for `context.user_data` from python-telegram-bot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.bot.i18n import Lang


@dataclass(slots=True)
class UserState:
    """Mutable per-user conversation state."""

    lang: Lang = "fa"

    # chat selection
    chat_id: int | None = None
    chat_title: str | None = None

    # time window (minutes)
    window_minutes: int | None = None

    # prompt + destination
    prompt: str | None = None
    destination: str | None = None

    # misc flags
    waiting_for: str | None = None  # e.g. "prompt", "destination", "window_custom"

    extra: dict[str, Any] = field(default_factory=dict)


class StateStore:
    """Trivial singleton store; one UserState per user."""

    def __init__(self) -> None:
        self._by_user: dict[int, UserState] = {}

    def get(self, user_id: int) -> UserState:
        if user_id not in self._by_user:
            self._by_user[user_id] = UserState()
        return self._by_user[user_id]

    def reset(self, user_id: int) -> None:
        self._by_user[user_id] = UserState()


store = StateStore()