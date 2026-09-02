# filepath: src/ai/providers/google_ai.py
"""Google AI Studio (Gemini) provider via google-genai."""

from __future__ import annotations

import json
import logging
import re

from google import genai
from google.genai import types

from src.ai.providers.base import Analyzer
from src.userbot.reader import FetchedMessage

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a strict message filter. You will be given a JSON array of messages "
    "(each with: id, sender_name, date, text) and a user prompt describing what to find.\n"
    "Return a JSON object: {\"matching_ids\": [<int>, ...]} listing ONLY the ids of "
    "messages that match the user's prompt. If none match, return {\"matching_ids\": []}.\n"
    "Rules:\n"
    "  - Do NOT invent ids; use only ids from the input.\n"
    "  - Do NOT include any commentary, explanation, or extra text.\n"
    "  - Output must be valid JSON parseable by Python's json.loads.\n"
)


class GoogleAIAnalyzer(Analyzer):
    name = "google_ai"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        log.info("Google AI analyzer ready (model=%s)", model)

    async def analyze(
        self, messages: list[FetchedMessage], prompt: str
    ) -> list[int]:
        if not messages:
            return []
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
        return _parse_matching_ids(content, allowed_ids={m.id for m in messages})


def _parse_matching_ids(content: str, *, allowed_ids: set[int]) -> list[int]:
    """Same parsing logic as the OpenRouter provider — keep in sync."""
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    raw = fenced.group(1) if fenced else content

    parsed: object
    try:
        parsed = json.loads(raw)
    except Exception:
        m = re.search(r"\[[^\[\]]*\]", raw)
        if not m:
            log.warning("Could not parse AI response: %r", content[:300])
            return []
        try:
            parsed = json.loads(m.group(0))
        except Exception:
            return []

    ids: list[int] = []
    if isinstance(parsed, dict):
        for key in ("matching_ids", "ids", "matches"):
            if key in parsed and isinstance(parsed[key], list):
                ids = [int(x) for x in parsed[key] if isinstance(x, (int, float))]
                break
        else:
            for v in parsed.values():
                if isinstance(v, list):
                    ids = [int(x) for x in v if isinstance(x, (int, float))]
                    break
    elif isinstance(parsed, list):
        ids = [int(x) for x in parsed if isinstance(x, (int, float))]

    return [i for i in ids if i in allowed_ids]