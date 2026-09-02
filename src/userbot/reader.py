# filepath: src/userbot/reader.py
"""
Message fetching utilities — read-only by construction.

Uses Telethon's `iter_messages` with offset_date-based pagination so it
can handle windows larger than 100 messages without blowing memory.

SLOW-READ MODE
==============
When `slow_read=True`, we apply TWO levels of pacing to keep the request
pattern human-like and avoid Telegram's anti-spam heuristics:

  1. FAST pacing — after every `fast_batch_size` messages, sleep
     `fast_batch_delay` seconds. Defaults: 10 msgs → 1s sleep
     (= ~10 messages/second).
  2. LONG pacing — after every `batch_size` messages, sleep
     `long_pause_delay` seconds. Defaults: 50 msgs → 5s sleep
     (a "thinking pause" like a human re-reading the chat).

For a 1000-message scan with defaults this gives:
  * ~100 fast pauses of 1s (100s total)
  * ~20 long pauses of 5s (100s total, OVERLAPPING with fast pauses —
    the long pause includes the fast pause that triggers it)
  * Effective throughput: ~10 messages/second, with a "human breath"
    every 5 seconds.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from telethon.tl.types import Message

from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)

# Sane fallbacks (used when no Settings are available, e.g. in tests).
DEFAULT_FAST_BATCH_SIZE = 10
DEFAULT_FAST_BATCH_DELAY = 1.0
DEFAULT_BATCH_SIZE = 50
DEFAULT_LONG_PAUSE_DELAY = 5.0


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
    slow_read: bool = True,
    fast_batch_size: int = DEFAULT_FAST_BATCH_SIZE,
    fast_batch_delay: float = DEFAULT_FAST_BATCH_DELAY,
    batch_size: int = DEFAULT_BATCH_SIZE,
    long_pause_delay: float = DEFAULT_LONG_PAUSE_DELAY,
) -> list[FetchedMessage]:
    """
    Fetch all messages from `entity` strictly newer than `since`.

    Pagination strategy:
      * We iterate forward in time (oldest → newest) using `offset_date=since`
        and `reverse=True`. This gives us messages strictly after `since`.
      * We cap the total number returned by `max_messages` to protect against
        runaway sessions. The bot never crashes on huge chats.

    Slow-read mode (default, recommended):
      * After every `fast_batch_size` messages, sleep `fast_batch_delay`
        seconds. Defaults: 10 msgs → 1s = ~10 msgs/sec.
      * After every `batch_size` messages, sleep `long_pause_delay` seconds
        (a "human breath" pause). Defaults: 50 msgs → 5s.
      * The long pause INCLUDES the fast pause that triggered it, so we
        don't double-sleep at batch_size boundaries.
    """
    out: list[FetchedMessage] = []
    log.info(
        "fetch_messages: entity=%s since=%s cap=%d slow_read=%s "
        "fast=%d/%.1fs long=%d/%.1fs",
        entity, since, max_messages, slow_read,
        fast_batch_size, fast_batch_delay,
        batch_size, long_pause_delay,
    )

    count = 0
    # Normalize `since` to naive UTC for fair comparison with Telethon
    # Message.date (which is usually naive).
    since_naive = since.replace(tzinfo=None) if since.tzinfo is not None else since

    async for raw in client.iter_messages(
        entity,
        offset_date=since,
        reverse=True,
        limit=max_messages,
    ):
        # iter_messages may yield empty service messages sometimes; skip.
        if not isinstance(raw, Message):
            continue
        # Normalize msg date the same way.
        msg_date = raw.date
        if msg_date is None:
            continue
        if msg_date.tzinfo is not None:
            msg_date = msg_date.replace(tzinfo=None)
        # Telethon's offset_date is inclusive; filter strictly newer.
        if msg_date <= since_naive:
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

        if not slow_read:
            continue

        # Slow-read pacing — two levels.
        # LONG pause supersedes the FAST pause at batch boundaries so we
        # don't double-sleep.
        if count % batch_size == 0:
            log.debug(
                "slow_read: LONG pause %.1fs after %d messages",
                long_pause_delay, count,
            )
            await asyncio.sleep(long_pause_delay)
        elif count % fast_batch_size == 0:
            log.debug(
                "slow_read: fast pause %.1fs after %d messages",
                fast_batch_delay, count,
            )
            await asyncio.sleep(fast_batch_delay)

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