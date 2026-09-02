# filepath: src/ai/providers/base.py
"""Abstract base for AI providers."""

from __future__ import annotations

import abc

from src.userbot.reader import FetchedMessage


class Analyzer(abc.ABC):
    """Abstract AI provider. Implementations: OpenRouter, Google AI Studio."""

    name: str = "base"

    @abc.abstractmethod
    async def analyze(
        self, messages: list[FetchedMessage], prompt: str
    ) -> dict[int, str]:
        """
        Return a mapping of message_id → short reason for messages that match.

        The return type is intentionally a dict (not a list of ints) so the
        digest can show "why" each message matched — much more useful than a
        bare id list. Empty ids that don't exist in `messages` are filtered.

        MUST return ONLY ids that exist in the input `messages` (defensive).
        MUST return a dict (possibly empty). MUST NOT raise on no-match.
        MAY raise on network/HTTP errors.

        Reasons should be very short (< 80 chars); they're shown alongside
        the message excerpt in the digest.
        """
        raise NotImplementedError