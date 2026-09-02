# filepath: src/ai/analyzer.py
"""
AI orchestrator with auto-detection of the provider from `.env`.

At startup we look at the configured API keys:
    * exactly one of OPENROUTER_API_KEY / GOOGLE_AI_API_KEY must be set
      (the `Settings` model_validator enforces this).
    * We then instantiate the matching analyzer.
"""

from __future__ import annotations

import logging
from typing import Protocol

from src.ai.providers.base import Analyzer
from src.userbot.reader import FetchedMessage

log = logging.getLogger(__name__)


class AIAnalyzer(Protocol):
    async def analyze(
        self, messages: list[FetchedMessage], prompt: str
    ) -> list[int]: ...


def build_analyzer() -> Analyzer:
    """Construct the right Analyzer from settings, with a startup log line."""
    # Lazy import: avoid pulling provider SDKs until we know we need them.
    from src.config import get_settings

    s = get_settings()
    if s.ai_provider == "openrouter":
        from src.ai.providers.openrouter import OpenRouterAnalyzer

        log.info(
            "AI Provider: OpenRouter (model=%s) — API key present=%s",
            s.ai_model,
            bool(s.openrouter_api_key),
        )
        return OpenRouterAnalyzer(api_key=s.openrouter_api_key or "", model=s.ai_model)
    if s.ai_provider == "google":
        from src.ai.providers.google_ai import GoogleAIAnalyzer

        log.info(
            "AI Provider: Google AI Studio (model=%s) — API key present=%s",
            s.ai_model,
            bool(s.google_ai_api_key),
        )
        return GoogleAIAnalyzer(api_key=s.google_ai_api_key or "", model=s.ai_model)

    raise RuntimeError("No AI provider configured — check Settings validation.")