# filepath: src/ai/providers/openrouter.py
"""OpenRouter provider (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
import re

import httpx
from openai import AsyncOpenAI

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
        return _parse_matching_ids(content, allowed_ids={m.id for m in messages})


def _parse_matching_ids(content: str, *, allowed_ids: set[int]) -> list[int]:
    """
    Extract a list of matching ids from the model output.

    Tolerant of common mistakes (model returns bare list instead of object,
    extra prose, etc.) — but always filters against `allowed_ids` so the
    model can't trick us into forwarding arbitrary ids.
    """
    # Strip code fences if present.
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    raw = fenced.group(1) if fenced else content

    # Try object first, then bare list.
    parsed: object
    try:
        parsed = json.loads(raw)
    except Exception:
        # Find first [...] in the text and parse that.
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
        # Most common: {"matching_ids": [...]}
        for key in ("matching_ids", "ids", "matches"):
            if key in parsed and isinstance(parsed[key], list):
                ids = [int(x) for x in parsed[key] if isinstance(x, (int, float))]
                break
        else:
            # Maybe the model returned {"ids": [...]} — already covered.
            # Last resort: any list-valued field.
            for v in parsed.values():
                if isinstance(v, list):
                    ids = [int(x) for x in v if isinstance(x, (int, float))]
                    break
    elif isinstance(parsed, list):
        ids = [int(x) for x in parsed if isinstance(x, (int, float))]

    # Final defense: only allow ids we actually fetched.
    return [i for i in ids if i in allowed_ids]