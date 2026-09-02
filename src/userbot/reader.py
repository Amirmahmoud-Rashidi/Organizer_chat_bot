# filepath: src/userbot/reader.py
"""
Message fetching utilities — read-only by construction.

Uses Telethon's `iter_messages` with offset_date-based pagination so it
can handle windows larger than 100 messages without blowing memory.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from telethon.tl.types import Message

from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)


@dataclass(slots=True)
class FetchedMessage:
    """A trimmed-down, JSON-friendly representation of a Telegram message."""

    id: int
    date: datetime
    sender_id: int | None
    sender_name: str | None
    text: str
    is_reply: bool
    reply_to_msg_id: int | None

    @classmethod
    def from_telethon(cls, m: Message) -> "FetchedMessage":
        sender_id: int | None = None
        sender_name: str | None = None
        if m.sender is not None:
            sender_id = getattr(m.sender, "id", None)
            # Many entity types expose first_name / title / username
            sender_name = (
                getattr(m.sender, "first_name", None)
                or getattr(m.sender, "title", None)
                or getattr(m.sender, "username", None)
            )
            if sender_id is not None and sender_name:
                sender_name = f"{sender_name} (id={sender_id})"
            elif sender_id is not None:
                sender_name = f"id={sender_id}"

        text: str = m.message or ""
        # Trim very long messages — most AI models have token limits.
        if len(text) > 4000:
            text = text[:4000] + "…"

        return cls(
            id=m.id,
            date=m.date,
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
            is_reply=bool(m.reply_to and m.reply_to.reply_to_msg_id),
            reply_to_msg_id=m.reply_to.reply_to_msg_id if m.reply_to else None,
        )


async def fetch_messages(
    client: ReadOnlyClient,
    entity: Any,
    since: datetime,
    *,
    max_messages: int = 1000,
) -> list[FetchedMessage]:
    """
    Fetch all messages from `entity` strictly newer than `since`.

    Pagination strategy:
      * We iterate forward in time (oldest → newest) using `offset_date=since`
        and `reverse=True`. This gives us messages strictly after `since`.
      * We cap the total number returned by `max_messages` to protect against
        runaway sessions. The bot never crashes on huge chats.
    """
    out: list[FetchedMessage] = []
    log.info("fetch_messages: entity=%s since=%s cap=%d", entity, since, max_messages)

    count = 0
    async for raw in client.iter_messages(
        entity,
        offset_date=since,
        reverse=True,
        limit=max_messages,
    ):
        # iter_messages may yield empty service messages sometimes; skip.
        if not isinstance(raw, Message):
            continue
        # Telethon's offset_date is inclusive; filter strictly newer.
        if raw.date <= since:
            continue
        out.append(FetchedMessage.from_telethon(raw))
        count += 1
        if count >= max_messages:
            log.warning(
                "fetch_messages: hit cap of %d messages for entity=%s — truncating",
                max_messages,
                entity,
            )
            break

    log.info("fetch_messages: collected %d messages", len(out))
    return out


async def list_dialogs(client: ReadOnlyClient, limit: int = 200) -> list[dict[str, Any]]:
    """Return a UI-friendly list of recent chats (for the bot interface)."""
    items: list[dict[str, Any]] = []
    async for d in client.iter_dialogs(limit=limit):
        entity = d.entity
        if entity is None:
            continue
        eid = getattr(entity, "id", None)
        items.append(
            {
                "id": eid,
                "title": d.title or "(no title)",
                "is_user": getattr(entity, "bot", None) is None
                and not getattr(entity, "megagroup", False)
                and not getattr(entity, "broadcast", False),
                "username": getattr(entity, "username", None),
                "unread": d.unread_count,
            }
        )
    return items