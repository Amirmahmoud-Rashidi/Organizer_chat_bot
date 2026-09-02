# filepath: src/bot/state.py
"""
In-memory per-user state.

Because the bot is single-user (hardcoded ALLOWED_USER_ID), this module just
holds a small dict keyed by the authorized user id. If we ever go multi-user,
swap the storage for `context.user_data` from python-telegram-bot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from src.bot.i18n import Lang

DeliveryMode = Literal["forward", "digest"]
PacePresetName = Literal["safe", "normal", "fast", "custom"]


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

    # delivery mode (forward | digest)
    delivery_mode: DeliveryMode = "digest"  # safe default

    # read pacing — adjustable in the bot UI
    pace_preset: PacePresetName = "normal"  # default = balanced

    # custom pace values (only used when pace_preset == "custom")
    # If None, fall back to the .env defaults.
    custom_fast_batch_size: int | None = None
    custom_fast_batch_delay: float | None = None
    custom_batch_size: int | None = None
    custom_long_pause_delay: float | None = None

    # misc flags
    waiting_for: str | None = None  # e.g. "prompt", "destination", "window_custom", "pace_custom"

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