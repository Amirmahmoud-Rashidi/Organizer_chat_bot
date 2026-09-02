# filepath: src/bot/prompt_history.py
"""
Prompt history persisted in Saved Messages of the SAME Telegram account.

Why Saved Messages?
    * Cross-device — visible in any Telegram client.
    * No external DB needed.
    * Privacy-friendly — stays on Telegram's servers, under the user's control.

Storage format
    Each prompt is a message in the `me` chat with the form:

        📌 Prompt — 2026-09-02 14:31:02

        <prompt text>

We then trim the Saved Messages so that only the most recent N prompts
remain. We do this by deleting older prompts via `delete_in_saved_messages`
(exposed by the wrapper exclusively for the `me` peer).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from telethon.tl.types import Message

from src.config import get_settings
from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)

_HEADER_LINE_RE = re.compile(r"^📌 Prompt — (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$")


@dataclass(slots=True)
class PromptEntry:
    msg_id: int
    timestamp: datetime
    text: str


def _format_header(now: datetime) -> str:
    return f"📌 Prompt — {now.strftime('%Y-%m-%d %H:%M:%S')}"


def _build_message_body(prompt: str) -> str:
    return f"{_format_header(datetime.now())}\n\n{prompt.strip()}"


async def save_prompt(client: ReadOnlyClient, prompt: str) -> int:
    """Append `prompt` to Saved Messages and trim history to N. Returns new msg id."""
    settings = get_settings()
    body = _build_message_body(prompt)
    sent = await client.send_to_self(body)
    log.info("Saved prompt (msg_id=%d) to Saved Messages", sent.id)

    # Trim — keep only the most recent N prompt messages.
    await _trim_history(client, keep=settings.prompt_history_limit)
    return sent.id


async def load_recent_prompts(client: ReadOnlyClient, limit: int | None = None) -> list[PromptEntry]:
    """
    Read the most recent prompts from Saved Messages.

    We scan the last `limit` messages (default = 3 * prompt_history_limit) and
    parse out any that match our header format, in chronological order.
    """
    settings = get_settings()
    cap = limit or settings.prompt_history_limit * 3
    out: list[PromptEntry] = []
    async for raw in client.iter_messages("me", limit=cap):
        if not isinstance(raw, Message):
            continue
        text = raw.message or ""
        parsed = _parse_prompt_message(raw.id, text)
        if parsed is not None:
            out.append(parsed)
    # iter_messages yields newest-first; return newest-first as well.
    return out


def _parse_prompt_message(msg_id: int, text: str) -> PromptEntry | None:
    lines = text.splitlines()
    if not lines:
        return None
    m = _HEADER_LINE_RE.match(lines[0].strip())
    if not m:
        return None
    try:
        ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    body = "\n".join(lines[1:]).strip()
    return PromptEntry(msg_id=msg_id, timestamp=ts, text=body)


async def _trim_history(client: ReadOnlyClient, *, keep: int) -> int:
    """Delete older prompt messages so only the newest `keep` remain."""
    # Collect all prompt messages (newest-first).
    prompts: list[PromptEntry] = []
    # Look at enough messages to cover the keep window plus some slack.
    async for raw in client.iter_messages("me", limit=max(keep * 3, 30)):
        if not isinstance(raw, Message):
            continue
        parsed = _parse_prompt_message(raw.id, raw.message or "")
        if parsed is not None:
            prompts.append(parsed)
    if len(prompts) <= keep:
        return 0
    # prompts are newest-first because iter_messages yields newest-first.
    to_delete = [p.msg_id for p in prompts[keep:]]
    if not to_delete:
        return 0
    log.info("Trimming prompt history: deleting %d older entries", len(to_delete))
    await client.delete_in_saved_messages(to_delete)
    return len(to_delete)