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
    """
    Extract {id: reason} mapping from the model output.

    Tolerant of common mistakes (bare list, extra prose, code fences, etc.).
    Always filters against `allowed_ids` so the model cannot trick us into
    referencing arbitrary ids.

    Backward-compat: also accepts the legacy `{"matching_ids": [...]}` or
    bare `[1,2,3]` shapes — for those, reason is empty.
    """
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    raw = fenced.group(1) if fenced else content

    parsed: object
    try:
        parsed = json.loads(raw)
    except Exception:
        # Try to recover by extracting the largest balanced {...} block.
        parsed = _extract_json_object(raw)
        if parsed is None:
            # Last resort: any array.
            m = re.search(r"\[[^\[\]]*\]", raw)
            if not m:
                log.warning("Could not parse AI response: %r", content[:300])
                return {}
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                return {}

    out: dict[int, str] = {}

    # Preferred shape: {"matches": [{"id": 1, "reason": "..."}, ...]}
    if isinstance(parsed, dict):
        # Find the list field — accept several common keys.
        list_value: list[object] | None = None
        for key in ("matches", "results", "matching"):
            if key in parsed and isinstance(parsed[key], list):
                list_value = parsed[key]
                break
        if list_value is None:
            # Backward-compat: legacy {"matching_ids": [...]} / {"ids": [...]}
            for key in ("matching_ids", "ids"):
                if key in parsed and isinstance(parsed[key], list):
                    list_value = parsed[key]
                    break
        if list_value is None:
            # Last resort: any list-valued field.
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
        # Bare list of ints — backward-compat.
        for item in parsed:
            if isinstance(item, (int, float)):
                out[int(item)] = ""

    # Final defense: only allow ids we actually fetched.
    return {i: r for i, r in out.items() if i in allowed_ids}