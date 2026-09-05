# filepath: src/userbot/summarizer.py
"""
Message summarizer — the SAFE alternative to forwarding.

Why this exists
===============
Forwarding (`forward_messages`) keeps the original "forwarded from" header,
which makes it look like spam-like behavior if you do it for many messages
in a short window. Plus, the destination chat has no easy way to tell which
messages matched vs which were noise.

This module does something much friendlier:
    * It builds a short, human-readable summary for each matching message:
        - a deep-link to the original message (works in any Telegram client),
        - the sender name + date,
        - a short excerpt of the message text.
    * It then SENDS a single combined report to the destination chat.

Result: the destination shows a neat digest of "what matched", with clickable
links. The original chat is completely untouched — this is even friendlier to
Telegram's anti-spam heuristics than forwarding.

NOTE on sending
===============
The `ReadOnlyClient` wrapper currently exposes only `send_to_self` (for
prompt history). We need to send to the destination chat too — so we
extend the wrapper with a narrowly-scoped `send_to_destination` method.
That method is hard-coded to ONLY accept a destination resolved from the
config/handler — it still cannot be used to message arbitrary peers.
"""

from __future__ import annotations

import logging
from typing import Any

from src.userbot.reader import FetchedMessage
from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)

# Telegram's hard limit for a single text message is 4096 chars. We leave a
# safety margin (entities, markdown, etc. can add a bit of overhead).
_TELEGRAM_MESSAGE_LIMIT = 4096
_SAFE_CHUNK_SIZE = 3900


def make_message_link(entity: Any, message_id: int) -> str | None:
    """
    Build a t.me deep-link to a specific message in `entity`.

    Format: https://t.me/c/<internal_id>/<msg_id> for supergroups/channels,
            https://t.me/<username>/<msg_id> for public chats,
            None for private 1:1 chats (no link possible).

    Note: the underlying numeric ID we have is the *bot-API* style id; for
    t.me links we need either the @username (public) or the channel's
    internal id (for private channels). We try our best; if we can't build
    a link we just return None and the summary will say "no link".
    """
    if entity is None:
        return None

    # Public chats: use @username
    username = getattr(entity, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"

    # Private supergroups/channels: use internal id.
    internal_id = getattr(entity, "id", None)
    # Telethon's Channel.id already includes the -100 prefix in some versions;
    # we normalize to the "c/<id>/<msg>" form which works everywhere.
    if internal_id is None:
        return None

    # Channel/supergroup IDs in t.me/c links need the absolute value WITHOUT the -100 prefix.
    s = str(internal_id)
    if s.startswith("-100"):
        bare = s[4:]
    elif s.startswith("-"):
        bare = s[1:]
    else:
        bare = s

    # Heuristic: only build the link if it looks like a channel/supergroup id (large number).
    try:
        if int(bare) < 10**9:  # too small to be a channel/supergroup
            return None
    except ValueError:
        return None

    return f"https://t.me/c/{bare}/{message_id}"


def build_digest(
    entity: Any,
    matched: list[tuple[FetchedMessage, str]],
    *,
    prompt: str,
    max_excerpt: int = 300,
) -> str:
    """
    Build the summary text for a set of matching messages.

    `matched` is a list of (FetchedMessage, ai_reason) pairs. The AI reason
    lets the user see WHY each message matched.
    """
    parts: list[str] = [
        f"🤖 **Organizer Bot** — {len(matched)} match(es)",
        f"**Prompt:** {prompt[:200]}{'…' if len(prompt) > 200 else ''}",
        "",
    ]
    for idx, (m, reason) in enumerate(matched, 1):
        link = make_message_link(entity, m.id)
        sender = m.sender_name or "unknown"
        date_str = m.date.strftime("%Y-%m-%d %H:%M") if m.date else "?"
        text = (m.text or "").strip()
        if len(text) > max_excerpt:
            text = text[:max_excerpt] + "…"

        parts.append(f"**{idx}.** [{sender} — {date_str}]({link})" if link else f"**{idx}.** {sender} — {date_str}")
        if text:
            parts.append(f"> {text}")
        if reason:
            parts.append(f"_Reason:_ {reason}")
        parts.append("")  # blank line between entries

    return "\n".join(parts).strip()


def _split_digest(text: str, *, max_len: int = _SAFE_CHUNK_SIZE) -> list[str]:
    """
    Split `text` into chunks that fit under Telegram's message size limit.

    We split on blank-line boundaries (each digest entry is separated by an
    empty line — see `build_digest`) so we never cut a message entry in half.
    If a single "paragraph" is somehow still too long (pathological case),
    it gets hard-split as a last resort.
    """
    if len(text) <= max_len:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_len:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(para) <= max_len:
            current = para
        else:
            # Last resort: a single paragraph is bigger than the limit.
            for i in range(0, len(para), max_len):
                chunks.append(para[i : i + max_len])

    if current:
        chunks.append(current)

    return chunks


async def send_digest(
    client: ReadOnlyClient,
    *,
    destination: Any,
    text: str,
) -> None:
    """
    Send the digest text to the destination chat.

    Splits into multiple messages if `text` exceeds Telegram's ~4096-char
    limit per message, so large digests never fail to send.
    """
    if not text:
        return

    chunks = _split_digest(text)
    total = len(chunks)
    log.info(
        "send_digest: sending %d-char digest to %s in %d part(s)",
        len(text), destination, total,
    )
    for i, chunk in enumerate(chunks, 1):
        body = chunk if total == 1 else f"({i}/{total})\n\n{chunk}"
        await client.send_to_destination(destination, body)
