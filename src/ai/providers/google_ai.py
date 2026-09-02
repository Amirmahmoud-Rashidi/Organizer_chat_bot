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
    "Return a JSON object: {\"matches\": [{\"id\": <int>, \"reason\": \"<short>\"}, ...]}\n"
    "listing ONLY the messages that match the user's prompt. If none match, return "
    "{\"matches\": []}.\n"
    "Rules:\n"
    "  - Do NOT invent ids; use only ids from the input.\n"
    "  - The `reason` field must be a SHORT (< 80 char) human-readable phrase "
    "explaining WHY the message matched (e.g. 'mentions job offer', 'has discount code').\n"
    "  - Do NOT include any commentary, explanation, or extra text outside the JSON.\n"
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
        return _parse_matches(content, allowed_ids={m.id for m in messages})


def _extract_json_object(text: str) -> object | None:
    """Find the first balanced {...} block in text and json.loads it."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    return None
    return None


def _parse_matches(content: str, *, allowed_ids: set[int]) -> dict[int, str]:
    """Same parsing logic as the OpenRouter provider — keep in sync."""
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    raw = fenced.group(1) if fenced else content

    parsed: object
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = _extract_json_object(raw)
        if parsed is None:
            m = re.search(r"\[[^\[\]]*\]", raw)
            if not m:
                log.warning("Could not parse AI response: %r", content[:300])
                return {}
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                return {}

    out: dict[int, str] = {}
    if isinstance(parsed, dict):
        list_value: list[object] | None = None
        for key in ("matches", "results", "matching"):
            if key in parsed and isinstance(parsed[key], list):
                list_value = parsed[key]
                break
        if list_value is None:
            for key in ("matching_ids", "ids"):
                if key in parsed and isinstance(parsed[key], list):
                    list_value = parsed[key]
                    break
        if list_value is None:
            for v in parsed.values():
                if isinstance(v, list):
                    list_value = v
                    break
        if list_value is None:
            return {}
        for item in list_value:
            if isinstance(item, dict):
                rid = item.get("id")
                if isinstance(rid, (int, float)):
                    reason = item.get("reason", "")
                    out[int(rid)] = str(reason)[:120] if reason else ""
            elif isinstance(item, (int, float)):
                out[int(item)] = ""
    elif isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, (int, float)):
                out[int(item)] = ""

    return {i: r for i, r in out.items() if i in allowed_ids}