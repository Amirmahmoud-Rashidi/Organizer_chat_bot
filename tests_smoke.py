"""Smoke tests for the Organizer Chat Bot.

Run:  .venv\\Scripts\\python.exe tests_smoke.py
"""
from __future__ import annotations

import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))


def setup_env(provider: str | None) -> None:
    os.environ["TELEGRAM_API_ID"] = "1"
    os.environ["TELEGRAM_API_HASH"] = "x"
    os.environ["BOT_TOKEN"] = "1:1"
    os.environ["ALLOWED_USER_ID"] = "1"
    os.environ["FORWARD_DESTINATION"] = "@x"
    if provider == "openrouter":
        os.environ["OPENROUTER_API_KEY"] = "sk-test"
        os.environ.pop("GOOGLE_AI_API_KEY", None)
    elif provider == "google":
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ["GOOGLE_AI_API_KEY"] = "ga-test"
    elif provider == "both":
        os.environ["OPENROUTER_API_KEY"] = "sk-test"
        os.environ["GOOGLE_AI_API_KEY"] = "ga-test"
    elif provider == "none":
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("GOOGLE_AI_API_KEY", None)


def test_ai_autodetect() -> None:
    import importlib

    print("\n=== AI auto-detect ===")
    for case in ("openrouter", "google"):
        setup_env(case)
        import src.config

        importlib.reload(src.config)
        s = src.config.get_settings()
        assert s.ai_provider == case, f"expected {case}, got {s.ai_provider}"
        print(f"  ok: only {case} -> ai_provider={s.ai_provider}")

    for case in ("both", "none"):
        setup_env(case)
        import src.config

        importlib.reload(src.config)
        try:
            src.config.get_settings()
            print(f"  FAIL: {case} was accepted")
            sys.exit(1)
        except Exception as exc:
            print(f"  ok: {case} rejected -> {str(exc).splitlines()[-1][:60]}")


def test_readonly_wrapper() -> None:
    print("\n=== ReadOnlyClient wrapper ===")
    from src.userbot.wrapper import ReadOnlyClient

    class FakeRaw:
        def get_entity(self, *a, **k):
            pass

        def get_me(self):
            pass

        def get_dialogs(self, *a, **k):
            pass

        def iter_messages(self, *a, **k):
            pass

        def iter_dialogs(self, *a, **k):
            pass

        def is_connected(self):
            return True

        async def start(self):
            pass

        async def disconnect(self):
            pass

        def forward_messages(self, *a, **k):
            pass

        def send_message(self, *a, **k):
            return "should-not-reach"

        def edit_message(self, *a, **k):
            return "should-not-reach"

        def delete_messages(self, *a, **k):
            return "should-not-reach"

    w = ReadOnlyClient.__new__(ReadOnlyClient)
    w._ReadOnlyClient__raw = FakeRaw()

    allowed = [
        "get_entity",
        "get_me",
        "get_dialogs",
        "iter_messages",
        "iter_dialogs",
        "is_connected",
        "forward_messages",
        "send_to_self",
        "delete_in_saved_messages",
    ]
    for m in allowed:
        assert hasattr(w, m), f"expected {m}"
    print(f"  ok: allowed methods present ({len(allowed)})")

    blocked = [
        "send_message",
        "edit_message",
        "delete_messages",
        "join_channel",
        "leave_channel",
        "pin_message",
        "unpin_message",
        "update_profile",
    ]
    for m in blocked:
        try:
            getattr(w, m)
            print(f"  FAIL: {m} leaked")
            sys.exit(1)
        except AttributeError:
            pass
    print(f"  ok: {len(blocked)} write methods blocked")


def test_ai_parser() -> None:
    print("\n=== AI JSON parser (id filtering) ===")
    from src.ai.providers.google_ai import _parse_matching_ids as G
    from src.ai.providers.openrouter import _parse_matching_ids as P

    allowed = {1, 2, 3}
    cases = [
        ('{"matching_ids":[1,3]}', [1, 3]),
        ('{"ids":[1]}', [1]),
        ('{"matching_ids":[1,999]}', [1]),
        ("[1,2,3]", [1, 2, 3]),
        ('{"matching_ids":[]}', []),
        ('Here you go: {"matching_ids":[2]}', [2]),
        ('```json\n{"matching_ids":[1,2]}\n```', [1, 2]),
        ("garbage", []),
        ('{"matching_ids":[1,"two",3]}', [1, 3]),
    ]
    for raw, expected in cases:
        a = P(raw, allowed_ids=allowed)
        g = G(raw, allowed_ids=allowed)
        assert a == expected, f"P failed: {raw!r} -> {a} != {expected}"
        assert g == expected, f"G failed: {raw!r} -> {g} != {expected}"
        print(f"  ok: {raw[:42]!r:48s} -> {expected}")


def test_i18n() -> None:
    print("\n=== i18n ===")
    from src.bot.i18n import format_window, parse_window, t

    assert t("welcome", "fa").startswith("👋")
    assert t("welcome", "en").startswith("👋")
    assert parse_window("48h") == 48 * 60
    assert parse_window("7d") == 7 * 24 * 60
    assert parse_window("1w") == 7 * 24 * 60
    assert parse_window("30m") == 30
    assert parse_window("bogus") is None
    assert format_window(60) == "1h"
    assert format_window(1440) == "1d"
    assert format_window(10080) == "1w"
    print("  ok: 2 languages + parse/format roundtrip")


def test_prompt_history_parsing() -> None:
    print("\n=== Prompt history parser ===")
    from src.bot.prompt_history import _parse_prompt_message

    valid = "📌 Prompt — 2026-09-02 14:31:02\n\nlook for job offers"
    parsed = _parse_prompt_message(msg_id=42, text=valid)
    assert parsed is not None
    assert parsed.msg_id == 42
    assert "job offers" in parsed.text
    assert parsed.timestamp.year == 2026

    invalid = "this is not a prompt message"
    assert _parse_prompt_message(msg_id=1, text=invalid) is None
    print("  ok: valid header parsed; garbage rejected")


def test_syntax() -> None:
    print("\n=== syntax check (py_compile) ===")
    import py_compile

    import pathlib

    for p in pathlib.Path("src").rglob("*.py"):
        py_compile.compile(str(p), doraise=True)
    print("  ok: every .py in src/ compiles")


def main() -> None:
    setup_env("openrouter")  # ensure a valid env before any import
    test_syntax()
    test_ai_autodetect()
    test_readonly_wrapper()
    test_ai_parser()
    test_i18n()
    test_prompt_history_parsing()
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()