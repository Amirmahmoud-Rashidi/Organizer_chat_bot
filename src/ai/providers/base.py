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
    ) -> list[int]:
        """
        Return a list of message ids (from `messages`) that match the prompt.

        MUST return ONLY ids that exist in the input `messages` (defensive).
        MUST return a list (possibly empty). MUST NOT raise on no-match.
        MAY raise on network/HTTP errors.
        """
        raise NotImplementedError