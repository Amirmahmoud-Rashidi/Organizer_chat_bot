# filepath: src/ai/providers/google_ai.py
"""Google AI Studio (Gemini) provider via google-genai."""

from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

from src.ai.providers._parsing import SYSTEM_PROMPT, parse_matches
from src.ai.providers.base import Analyzer
from src.userbot.reader import FetchedMessage

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = SYSTEM_PROMPT

# Backward-compat aliases: parsing logic now lives in `_parsing.py` (shared
# with openrouter.py) but keep the old private names importable, since some
# tests/tools import them directly from this module.
_parse_matches = parse_matches


class GoogleAIAnalyzer(Analyzer):
    name = "google_ai"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        log.info("Google AI analyzer ready (model=%s)", model)

    async def analyze(
        self, messages: list[FetchedMessage], prompt: str
    ) -> dict[int, str]:
        if not messages:
            return {}
        payload = [
            {
                "id": m.id,
                "sender_name": m.sender_name,
                "date": m.date.isoformat() if m.date else None,
                "text": m.text,
            }
            for m in messages
        ]
        user_text = (
            f"PROMPT:\n{prompt}\n\n"
            f"MESSAGES (JSON):\n{json.dumps(payload, ensure_ascii=False)}"
        )

        config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.0,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_text,
                config=config,
            )
        except Exception:
            log.exception("Google AI API call failed")
            raise

        content = response.text or "{}"
        return parse_matches(content, allowed_ids={m.id for m in messages})
