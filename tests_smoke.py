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
    print("\n=== AI JSON parser (dict + reasons) ===")
    from src.ai.providers.google_ai import _parse_matches as G
    from src.ai.providers.openrouter import _parse_matches as P

    allowed = {1, 2, 3}
    # Each case: (raw, expected_dict)
    cases = [
        # New shape
        ('{"matches":[{"id":1,"reason":"job offer"},{"id":3,"reason":"discount"}]}',
         {1: "job offer", 3: "discount"}),
        ('{"results":[{"id":2,"reason":"x"}]}', {2: "x"}),
        ('{"matches":[]}', {}),
        # Backward-compat
        ('{"matching_ids":[1,3]}', {1: "", 3: ""}),
        ('{"ids":[1]}', {1: ""}),
        ('[1,2,3]', {1: "", 2: "", 3: ""}),
        # Mixed types / filtering
        ('{"matches":[{"id":1,"reason":"a"},{"id":999,"reason":"fake"}]}',
         {1: "a"}),
        ('{"matches":[{"id":1,"reason":42}]}', {1: "42"}),
        ('Here you go: {"matches":[{"id":2,"reason":"r"}]}', {2: "r"}),
        ('```json\n{"matches":[{"id":1,"reason":"a"}]}\n```', {1: "a"}),
        ("garbage", {}),
        ('{"matches":[{"id":"two"}]}', {}),
    ]
    for raw, expected in cases:
        a = P(raw, allowed_ids=allowed)
        g = G(raw, allowed_ids=allowed)
        assert a == expected, f"P failed: {raw!r} -> {a} != {expected}"
        assert g == expected, f"G failed: {raw!r} -> {g} != {expected}"
        print(f"  ok: {raw[:48]!r:54s} -> {expected}")


def test_message_links() -> None:
    print("\n=== t.me deep-link builder ===")
    from src.userbot.summarizer import make_message_link

    class PublicEntity:
        username = "my_channel"
        id = 1234567890

    class PrivateChannel:
        username = None
        id = -1001234567890

    class PrivateChat:
        username = None
        id = 987654321  # small, looks like user id

    class NoId:
        pass

    assert make_message_link(PublicEntity(), 42) == "https://t.me/my_channel/42"
    assert make_message_link(PrivateChannel(), 99) == "https://t.me/c/1234567890/99"
    assert make_message_link(PrivateChat(), 1) is None
    assert make_message_link(None, 1) is None
    assert make_message_link(NoId(), 1) is None
    print("  ok: public + private channel + private chat + edge cases")


def test_digest_builder() -> None:
    print("\n=== Digest builder ===")
    from datetime import datetime
    from src.userbot.summarizer import build_digest
    from src.userbot.reader import FetchedMessage

    class Entity:
        username = "test_chan"
        id = 123

    matches = [
        (FetchedMessage(1, datetime(2026, 9, 2, 10, 0), 111, "Alice", "Hello world", False, None),
         "greeting"),
        (FetchedMessage(2, datetime(2026, 9, 2, 11, 0), 222, "Bob", "x" * 500, False, None),
         "long text"),
    ]
    text = build_digest(Entity(), matches, prompt="looking for greetings")
    assert "Organizer Bot" in text
    assert "2 match" in text
    assert "Alice" in text
    assert "Bob" in text
    assert "https://t.me/test_chan/1" in text
    assert "https://t.me/test_chan/2" in text
    # Long text should be truncated
    assert "x" * 500 not in text
    assert "…" in text
    # Reasons included
    assert "greeting" in text
    assert "long text" in text
    print("  ok: digest contains sender + link + truncated excerpt + reason")


def test_proxy_config() -> None:
    """Validate the proxy feature is OFF by default and only activates when set."""
    print("\n=== Proxy config (feature-flagged) ===")
    import importlib
    from src import config as cfg_mod

    # Case 1: proxy disabled (default)
    setup_env("openrouter")
    for k in ("TELEGRAM_PROXY_ENABLED",):
        os.environ[k] = "false"
    for k in ("TELEGRAM_PROXY_HOST", "TELEGRAM_PROXY_PORT"):
        os.environ.pop(k, None)
    importlib.reload(cfg_mod)
    s = cfg_mod.get_settings()
    assert s.telegram_proxy_enabled is False
    assert _build_proxy() is None
    print("  ok: default config -> proxy disabled, _build_proxy() returns None")

    # Case 2: proxy enabled with SOCKS5
    os.environ["TELEGRAM_PROXY_ENABLED"] = "true"
    os.environ["TELEGRAM_PROXY_TYPE"] = "socks5"
    os.environ["TELEGRAM_PROXY_HOST"] = "127.0.0.1"
    os.environ["TELEGRAM_PROXY_PORT"] = "1080"
    os.environ["TELEGRAM_PROXY_USERNAME"] = "alice"
    os.environ["TELEGRAM_PROXY_PASSWORD"] = "secret"
    importlib.reload(cfg_mod)
    s = cfg_mod.get_settings()
    assert s.telegram_proxy_enabled is True
    proxy = _build_proxy()
    assert proxy is not None
    assert proxy[0] == "socks5"
    assert proxy[1] == "127.0.0.1"
    assert proxy[2] == 1080
    assert proxy[3] is True  # rdns
    assert proxy[4] == "alice"  # username
    assert proxy[5] == "secret"  # password
    print("  ok: SOCKS5 proxy -> ('socks5', '127.0.0.1', 1080, True, 'alice', 'secret')")

    # Case 3: proxy enabled with HTTP (no auth)
    os.environ["TELEGRAM_PROXY_TYPE"] = "http"
    os.environ["TELEGRAM_PROXY_USERNAME"] = ""
    os.environ["TELEGRAM_PROXY_PASSWORD"] = ""
    importlib.reload(cfg_mod)
    s = cfg_mod.get_settings()
    proxy = _build_proxy()
    assert proxy == ("http", "127.0.0.1", 1080)
    print("  ok: HTTP proxy -> ('http', '127.0.0.1', 1080)")

    # Case 4: enabled but missing port -> pydantic type-coercion error
    # (pydantic rejects empty string for int, which is fine for our purposes)
    os.environ["TELEGRAM_PROXY_PORT"] = ""
    importlib.reload(cfg_mod)
    raised = False
    try:
        cfg_mod.get_settings()
    except Exception:
        raised = True
    assert raised, "missing port should have raised"
    print("  ok: missing port -> pydantic rejected (validation working)")


def _build_proxy():
    """Test-local wrapper around the production helper."""
    from src.userbot.client import _build_proxy as real
    return real()


def test_https_proxy_autodetect() -> None:
    """setup_https_proxy() detects a listening HTTP proxy on localhost."""
    print("\n=== setup_https_proxy() auto-detect ===")
    import socket
    import threading
    from src import main as main_mod

    # Start a tiny HTTP server on a free port in a background thread.
    probe_port = 18765
    import http.server
    import socketserver

    class _QuietHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):  # silence
            pass

        def do_CONNECT(self):  # not used, but harmless
            self.send_response(200)
            self.end_headers()

        def do_GET(self):  # needed because probes use HTTP CONNECT, but harmless if not
            self.send_response(200)
            self.end_headers()

    httpd = socketserver.TCPServer(("127.0.0.1", probe_port), _QuietHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        # Make sure we start with a clean env
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            os.environ.pop(k, None)
        # Also reset the module-level port-probe list to include our port
        main_mod._PROXY_PROBES.append(("127.0.0.1", probe_port, "test probe"))
        main_mod.setup_https_proxy()
        assert os.environ.get("HTTPS_PROXY") == f"http://127.0.0.1:{probe_port}", \
            f"expected proxy to be set, got {os.environ.get('HTTPS_PROXY')}"
        print(f"  ok: detected listener on 127.0.0.1:{probe_port} -> set HTTPS_PROXY")
    finally:
        httpd.shutdown()
        httpd.server_close()
        # Clean up env so other tests aren't affected
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            os.environ.pop(k, None)
        # Restore the probe list
        main_mod._PROXY_PROBES.pop()


def test_presets() -> None:
    print("\n=== Read-pace presets ===")
    from src.bot.presets import (
        PRESET_SAFE, PRESET_NORMAL, PRESET_FAST,
        all_presets, get_preset,
    )

    # All three exist
    names = {p.name_preset for p in all_presets()}
    assert names == {"safe", "normal", "fast"}, f"unexpected presets: {names}"

    # Rate ordering: safe < normal < fast
    assert PRESET_SAFE.rate_per_second() < PRESET_NORMAL.rate_per_second() < PRESET_FAST.rate_per_second()
    print(
        f"  ok: rate order safe({PRESET_SAFE.rate_per_second():.1f}) "
        f"< normal({PRESET_NORMAL.rate_per_second():.1f}) "
        f"< fast({PRESET_FAST.rate_per_second():.1f}) msgs/sec"
    )

    # Each preset has sane values
    for p in (PRESET_SAFE, PRESET_NORMAL, PRESET_FAST):
        assert p.slow_read_enabled is True
        assert p.fast_batch_size >= 1
        assert p.fast_batch_delay > 0
        assert p.batch_size >= p.fast_batch_size
        assert p.long_pause_delay >= 0
        # Bilingual labels exist
        assert p.label_fa and p.label_en
        assert p.desc_fa and p.desc_en
    print("  ok: each preset has valid bilingual labels + sane values")

    # Default fallback
    assert get_preset("nonexistent").name_preset == "normal"
    assert get_preset("safe").name_preset == "safe"
    print("  ok: get_preset falls back to 'normal' for unknown names")


def test_presets_integration_with_fetch() -> None:
    """Verify that fetch_messages honors a preset's pacing values."""
    import asyncio
    from datetime import datetime
    from src.bot import presets as p_mod
    from src.bot.presets import PRESET_SAFE, PRESET_FAST
    from src.userbot import reader as reader_mod
    from src.userbot.reader import fetch_messages
    from telethon.tl.types import Message

    class FakeClient:
        def __init__(self, total):
            self._total = total

        async def iter_messages(self, entity, **_kw):
            for i in range(1, self._total + 1):
                yield Message(
                    id=i, peer_id=None,
                    date=datetime(2026, 9, 2, 10, 0),
                    message=f"msg {i}",
                )

    sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def spy_sleep(delay: float) -> None:
        sleeps.append(delay)
        await real_sleep(0)

    reader_mod.asyncio.sleep = spy_sleep

    async def run() -> None:
        since = datetime(2020, 1, 1)
        # 20 msgs with SAFE preset (batch=1, delay=1, long=20/10s)
        sleeps.clear()
        await fetch_messages(
            FakeClient(20), entity=1, since=since,
            slow_read=PRESET_SAFE.slow_read_enabled,
            fast_batch_size=PRESET_SAFE.fast_batch_size,
            fast_batch_delay=PRESET_SAFE.fast_batch_delay,
            batch_size=PRESET_SAFE.batch_size,
            long_pause_delay=PRESET_SAFE.long_pause_delay,
        )
        # 20 fast pauses of 1s (one per msg) + 1 long of 10s at msg 20
        n_fast = sum(1 for s in sleeps if s == 1.0)
        n_long = sum(1 for s in sleeps if s == 10.0)
        assert n_fast == 19, f"SAFE: expected 19 fast (every msg), got {n_fast} (sleeps={sleeps})"
        assert n_long == 1, f"SAFE: expected 1 long at msg 20, got {n_long} (sleeps={sleeps})"
        print(
            f"  ok: SAFE preset over 20 msgs -> 19×1s + 1×10s "
            f"(rate ~1 msg/sec + breath at 20)"
        )

        # 19 msgs with FAST preset (batch=20, delay=0.5, long=100/3s) -> no pacing triggered
        # (20 % 20 == 0 would trigger fast; 19 doesn't)
        sleeps.clear()
        await fetch_messages(
            FakeClient(19), entity=1, since=since,
            slow_read=PRESET_FAST.slow_read_enabled,
            fast_batch_size=PRESET_FAST.fast_batch_size,
            fast_batch_delay=PRESET_FAST.fast_batch_delay,
            batch_size=PRESET_FAST.batch_size,
            long_pause_delay=PRESET_FAST.long_pause_delay,
        )
        # 19 msgs: no fast (19 % 20 != 0), no long (19 < 100)
        assert sleeps == [], f"FAST: expected no pauses, got {sleeps}"
        print("  ok: FAST preset over 19 msgs -> 0 pauses (under batch size)")

    try:
        asyncio.run(run())
    finally:
        reader_mod.asyncio.sleep = real_sleep


def test_slow_read() -> None:
    """Test the two-level slow_read pacing using a sleep spy.

    We monkey-patch `asyncio.sleep` in the reader module to record what
    duration was requested. Then we check the *pattern* of sleeps rather
    than wall-clock time (which is unreliable on Windows/slow CI).
    """
    import asyncio
    from datetime import datetime
    from src.userbot import reader as reader_mod
    from src.userbot.reader import fetch_messages
    from telethon.tl.types import Message

    class FakeClient:
        def __init__(self, total: int) -> None:
            self._total = total

        async def iter_messages(self, entity, **_kw):
            for i in range(1, self._total + 1):
                yield Message(
                    id=i, peer_id=None,
                    date=datetime(2026, 9, 2, 10, 0),
                    message=f"msg {i}",
                )

    sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def spy_sleep(delay: float) -> None:
        sleeps.append(delay)
        await real_sleep(0)  # don't actually wait

    # Monkey-patch for the duration of the test
    reader_mod.asyncio.sleep = spy_sleep

    async def run() -> None:
        since = datetime(2020, 1, 1)

        # ---- Case A: slow_read disabled -> NO sleeps recorded
        sleeps.clear()
        result = await fetch_messages(
            FakeClient(60), entity=1, since=since,
            slow_read=False,
        )
        assert len(result) == 60
        assert sleeps == [], f"slow_read=False should not sleep, got {sleeps}"
        print("    slow_read=False: 0 sleeps recorded (correct)")

        # ---- Case B: scaled-down defaults, 60 msgs
        # fast_batch=5 / batch_size=50; 60 msgs.
        # Expected sleeps at msgs: 5,10,15,20,25,30,35,40,45,50(LONG replaces fast),55,60
        # = 11 fast + 1 long
        # (long at msg 50 supersedes the fast pause there; msgs 55 & 60 still trigger fast)
        sleeps.clear()
        result = await fetch_messages(
            FakeClient(60), entity=1, since=since,
            slow_read=True,
            fast_batch_size=5, fast_batch_delay=0.02,
            batch_size=50, long_pause_delay=0.05,
        )
        assert len(result) == 60
        n_fast = sum(1 for s in sleeps if s == 0.02)
        n_long = sum(1 for s in sleeps if s == 0.05)
        # 11 fast: msgs 5,10,15,20,25,30,35,40,45,55,60 (50 is taken by long)
        assert n_fast == 11, f"expected 11 fast pauses, got {n_fast} (sleeps={sleeps})"
        assert n_long == 1, f"expected 1 long pause, got {n_long} (sleeps={sleeps})"
        # Long must be at index 9 (i.e. 10th sleep = msg 50)
        long_indices = [i for i, s in enumerate(sleeps) if s == 0.05]
        assert long_indices == [9], f"long pause at index 9 (msg 50), got {long_indices}"
        # No double-sleep at boundary: msg 50 has long ONLY, not long+fast
        print(
            f"    slow_read=True, 60 msgs: 11 fast + 1 long "
            f"(long at msg 50, NO double-sleep — verified by index)"
        )

        # ---- Case C: production defaults, 10 msgs -> 1 fast pause at 1s
        sleeps.clear()
        result = await fetch_messages(
            FakeClient(10), entity=1, since=since,
            slow_read=True,
            fast_batch_size=10, fast_batch_delay=1.0,
            batch_size=50, long_pause_delay=5.0,
        )
        assert len(result) == 10
        # 1 fast at msg 10 (1.0s), no long (50 not reached)
        assert sleeps == [1.0], f"expected [1.0], got {sleeps}"
        print(f"    prod defaults, 10 msgs: sleeps={sleeps} (confirms 10 msgs/sec rate)")

        # ---- Case D: 50 msgs with prod defaults -> 4 fast + 1 long (long supersedes fast)
        sleeps.clear()
        result = await fetch_messages(
            FakeClient(50), entity=1, since=since,
            slow_read=True,
            fast_batch_size=10, fast_batch_delay=1.0,
            batch_size=50, long_pause_delay=5.0,
        )
        assert len(result) == 50
        # Without the supersede: 5 fast at 10,20,30,40,50 + 1 long at 50 = 6 sleeps
        # With the supersede: 4 fast at 10,20,30,40 + 1 long at 50 = 5 sleeps
        n_fast = sum(1 for s in sleeps if s == 1.0)
        n_long = sum(1 for s in sleeps if s == 5.0)
        assert n_fast == 4, f"expected 4 fast pauses, got {n_fast} (sleeps={sleeps})"
        assert n_long == 1, f"expected 1 long pause, got {n_long} (sleeps={sleeps})"
        # Total should be 4*1 + 1*5 = 9s
        total = sum(sleeps)
        assert total == 9.0, f"expected 9s total, got {total}s (sleeps={sleeps})"
        print(f"    prod defaults, 50 msgs: {len(sleeps)} sleeps totaling {total}s (4 fast + 1 long)")

    try:
        asyncio.run(run())
    finally:
        reader_mod.asyncio.sleep = real_sleep

    print("  ok: slow_read pacing (fast + long, no double-sleep at boundary)")


def test_wrapper_send_to_destination() -> None:
    """send_to_destination must exist; general send_message must NOT."""
    print("\n=== ReadOnlyClient: send_to_destination exposed ===")
    from src.userbot.wrapper import ReadOnlyClient

    class FakeRaw:
        def get_me(self): pass
        def send_message(self, *a, **k): return "raw send"
        def get_entity(self, *a, **k): pass
        def get_dialogs(self, *a, **k): pass
        def iter_messages(self, *a, **k): pass
        def iter_dialogs(self, *a, **k): pass
        def is_connected(self): return True
        def forward_messages(self, *a, **k): pass

    w = ReadOnlyClient.__new__(ReadOnlyClient)
    w._ReadOnlyClient__raw = FakeRaw()

    assert hasattr(w, "send_to_destination"), "missing send_to_destination"
    assert hasattr(w, "send_to_self"), "missing send_to_self"
    # send_message (raw) must NOT be exposed
    try:
        getattr(w, "send_message")
        assert False, "send_message leaked"
    except AttributeError:
        pass
    print("  ok: send_to_destination exposed, send_message blocked")


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
    test_wrapper_send_to_destination()
    test_ai_parser()
    test_message_links()
    test_digest_builder()
    test_proxy_config()
    test_https_proxy_autodetect()
    test_presets()
    test_presets_integration_with_fetch()
    test_slow_read()
    test_i18n()
    test_prompt_history_parsing()
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()