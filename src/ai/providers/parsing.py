# filepath: src/ai/providers/_parsing.py
"""
Shared response-parsing helpers for AI providers.

Both OpenRouterAnalyzer and GoogleAIAnalyzer send the same system prompt and
expect the same JSON shape back, so the parsing logic is centralized here
instead of being duplicated (and drifting) across provider modules.
"""

from __future__ import annotations

import json
import logging
import re

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
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


def extract_json_object(text: str) -> object | None:
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


def parse_matches(content: str, *, allowed_ids: set[int]) -> dict[int, str]:
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
        parsed = extract_json_object(raw)
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
