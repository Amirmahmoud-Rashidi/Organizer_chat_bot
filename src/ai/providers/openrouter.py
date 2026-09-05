# filepath: src/ai/providers/openrouter.py
"""OpenRouter provider (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging

import httpx
from openai import AsyncOpenAI

from src.ai.providers._parsing import SYSTEM_PROMPT, parse_matches
from src.ai.providers.base import Analyzer
from src.userbot.reader import FetchedMessage

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = SYSTEM_PROMPT

# Backward-compat aliases: parsing logic now lives in `_parsing.py` (shared
# with google_ai.py) but keep the old private names importable, since some
# tests/tools import them directly from this module.
_parse_matches = parse_matches


class OpenRouterAnalyzer(Analyzer):
    name = "openrouter"

    def __init__(self, api_key: str, model: str) -> None:
        # OpenRouter is OpenAI-compatible; we point base_url there.
        # We pass a custom httpx.AsyncClient because openai==1.54.4 still uses
        # the deprecated `proxies=` kwarg internally, which httpx>=0.28 rejects.
        # Using our own http_client avoids that incompatibility cleanly.
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            http_client=httpx.AsyncClient(),
        )
        self._model = model
        log.info("OpenRouter analyzer ready (model=%s)", model)

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
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
        except Exception:
            log.exception("OpenRouter API call failed")
            raise

        content = response.choices[0].message.content or "{}"
        return parse_matches(content, allowed_ids={m.id for m in messages})
