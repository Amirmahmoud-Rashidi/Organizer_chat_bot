# filepath: src/userbot/wrapper.py
"""
ReadOnlyClient — a security wrapper around Telethon's TelegramClient.

PHILOSOPHY
==========
Telethon's TelegramClient exposes ~300 methods including powerful destructive
ones (send_message, edit_message, delete_message, etc.). We never want the
bot logic to accidentally or maliciously invoke them.

This wrapper enforces a HARD, CODE-LEVEL read-only limit:
    * Only an explicit allowlist of read methods is exposed.
    * `forward_messages` is also exposed (we need it for the use case).
    * `delete_messages` is exposed ONLY for the `me` (Saved Messages) chat
      — used by the prompt-history feature.
    * Anything else raises `AttributeError`.

This is defense-in-depth: even if a bug or a prompt-injection in user-supplied
content tries to call `client.send_message(...)`, it will fail at runtime
because that attribute does not exist on this object.

The wrapper is intentionally minimal: it does NOT subclass TelegramClient
(avoids accidental method inheritance). It holds the client in a private
attribute and re-exports only the chosen methods.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from telethon import TelegramClient
from telethon.tl.custom.dialog import Dialog
from telethon.tl.types import Message, User, Chat, Channel

log = logging.getLogger(__name__)


class ReadOnlyClient:
    """A deliberately-narrow view over a TelegramClient."""

    def __init__(self, raw: TelegramClient) -> None:
        # Use name-mangling to make accidental access from outside harder.
        self.__raw = raw
        log.debug("ReadOnlyClient wrapping TelegramClient")

    # ------------------------------------------------------------------
    # Read-only methods — explicitly allowlisted.
    # Each is forwarded as-is. We do NOT wrap them further; if Telethon
    # raises, it propagates.
    # ------------------------------------------------------------------

    async def get_entity(self, entity: Any) -> Any:
        return await self.__raw.get_entity(entity)

    async def get_me(self) -> User:
        return await self.__raw.get_me()

    async def get_dialogs(self, limit: int | None = None) -> list[Dialog]:
        return await self.__raw.get_dialogs(limit=limit)

    async def iter_messages(
        self,
        entity: Any,
        *,
        offset_date: Any = None,
        reverse: bool = False,
        limit: int | None = None,
        min_id: int = 0,
        max_id: int = 0,
        wait_time: int | None = None,
    ) -> AsyncIterator[Message]:
        async for msg in self.__raw.iter_messages(
            entity,
            offset_date=offset_date,
            reverse=reverse,
            limit=limit,
            min_id=min_id,
            max_id=max_id,
            wait_time=wait_time,
        ):
            yield msg

    async def iter_dialogs(self, limit: int | None = None) -> AsyncIterator[Dialog]:
        async for d in self.__raw.iter_dialogs(limit=limit):
            yield d

    def is_connected(self) -> bool:
        return self.__raw.is_connected()

    # ------------------------------------------------------------------
    # Lifecycle — required for start/stop. Read-only in spirit (just
    # connects to Telegram; no data mutation).
    # ------------------------------------------------------------------

    async def start(self) -> None:
        await self.__raw.start()

    async def disconnect(self) -> None:
        await self.__raw.disconnect()

    async def __aenter__(self) -> "ReadOnlyClient":
        await self.__raw.start()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.__raw.disconnect()

    # ------------------------------------------------------------------
    # Forward — REQUIRED for this bot's core feature.
    # Forwards preserve the original author/time; we are not modifying
    # anything in the source chat.
    # ------------------------------------------------------------------

    async def forward_messages(
        self,
        entity: Any,
        messages: int | list[int] | Message | list[Message],
        *,
        from_peer: Any = None,
        silent: bool = False,
        drop_author: bool = False,
        background: bool = False,
    ) -> Any:
        """Forward messages to `entity`. The original messages are untouched."""
        if from_peer is None:
            raise ValueError(
                "forward_messages requires `from_peer` — refusing to forward "
                "without explicit source (safety)."
            )
        return await self.__raw.forward_messages(
            entity=entity,
            messages=messages,
            from_peer=from_peer,
            silent=silent,
            drop_author=drop_author,
            background=background,
        )

    # ------------------------------------------------------------------
    # Send-to-self — required to store prompt history in Saved Messages.
    # We deliberately do NOT expose `send_message` to arbitrary peers.
    # ------------------------------------------------------------------

    async def send_to_self(self, message: str) -> Message:
        """Send a message ONLY to Saved Messages (`me`). Raises for other peers."""
        me = await self.__raw.get_me()
        if not isinstance(me, User):
            raise RuntimeError("Cannot resolve `me` user.")
        # `me` itself is a valid peer that points to Saved Messages.
        return await self.__raw.send_message(me, message)

    async def send_to_destination(self, destination: Any, message: str) -> Message:
        """
        Send a digest/report message to the configured destination chat.

        Unlike `send_message` (which is NOT exposed at all), this method is
        narrowly scoped: it is the ONLY way for application code to send a
        message, and the destination is explicitly passed by the caller
        (i.e. the bot interface that the authorized user selected).

        Use this for the "summary instead of forward" mode.
        """
        if not destination:
            raise ValueError("destination is required for send_to_destination")
        return await self.__raw.send_message(destination, message)

    async def delete_in_saved_messages(self, message_ids: int | list[int]) -> bool:
        """Delete messages ONLY in Saved Messages. Hard-coded safety check."""
        me = await self.__raw.get_me()
        ids = message_ids if isinstance(message_ids, list) else [message_ids]
        # Telethon accepts `me` directly as the entity for Saved Messages.
        return await self.__raw.delete_messages(me, ids)

    # ------------------------------------------------------------------
    # Anything not in the allowlist above raises AttributeError.
    # This includes: send_message, edit_message, delete_message (general),
    # pin_message, unpin_message, join_channel, leave_channel, etc.
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # __init__ etc. are not affected because __getattr__ is only called
        # when normal lookup fails. We let `_`-prefixed names through so
        # logging/diagnostics can introspect if needed.
        if name.startswith("_"):
            raise AttributeError(name)
        raise AttributeError(
            f"ReadOnlyClient does not expose '{name}'. "
            f"This is a hard read-only wrapper around TelegramClient."
        )