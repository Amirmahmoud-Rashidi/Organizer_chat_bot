# filepath: src/userbot/forwarder.py
"""
Safe forwarding helper.

`forward_messages` preserves the original message's author/timestamp — exactly
what we want, because we're not modifying or rewriting content.
"""

from __future__ import annotations

import logging
from typing import Any

from telethon.tl.types import Message

from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)


async def forward_messages(
    client: ReadOnlyClient,
    *,
    destination: Any,
    source_entity: Any,
    message_ids: list[int],
    silent: bool = False,
) -> list[Message]:
    """Forward a batch of message IDs from `source_entity` to `destination`."""
    if not message_ids:
        return []
    log.info(
        "forwarding %d messages from %s to %s",
        len(message_ids),
        source_entity,
        destination,
    )
    result = await client.forward_messages(
        entity=destination,
        messages=message_ids,
        from_peer=source_entity,
        silent=silent,
    )
    # Telethon may return a single Message or a list depending on input.
    if isinstance(result, list):
        return [m for m in result if isinstance(m, Message)]
    if isinstance(result, Message):
        return [result]
    return []