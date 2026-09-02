# filepath: src/userbot/client.py
"""
Telethon client factory.

Creates and logs in the underlying `TelegramClient`. The returned raw client
should be wrapped by `ReadOnlyClient` (see `wrapper.py`) before being passed
to any application code. NEVER expose the raw client to the bot interface.
"""

from __future__ import annotations

import logging
import os

from telethon import TelegramClient

from src.config import get_settings

log = logging.getLogger(__name__)

# Where to place session files.
# - Default: `./data` (relative to the current working directory). This works
#   both on a local install AND inside Docker — in Docker the compose file
#   mounts `./data` from the host into `/app/data`, but inside the container
#   our CWD is `/app`, so `./data` resolves to `/app/data` either way.
# - Override: set TELEGRAM_SESSION_DIR=/some/path if you want it elsewhere.
_SESSION_DIR = os.environ.get("TELEGRAM_SESSION_DIR", "./data")


def _build_proxy() -> tuple | None:
    """
    Build a Telethon-compatible proxy tuple from settings, or None.

    Telethon expects:
      * SOCKS5: (socks5, host, port, rdns=True, username=None, password=None)
      * HTTP:   ("http", host, port)

    Returns None when proxy is disabled or unconfigured.
    """
    s = get_settings()
    if not s.telegram_proxy_enabled:
        return None
    if not s.telegram_proxy_host or not s.telegram_proxy_port:
        return None
    if s.telegram_proxy_type == "socks5":
        log.info(
            "Telethon proxy: SOCKS5 %s:%d (rdns=%s)",
            s.telegram_proxy_host, s.telegram_proxy_port, s.telegram_proxy_rdns,
        )
        return (
            "socks5",
            s.telegram_proxy_host,
            s.telegram_proxy_port,
            s.telegram_proxy_rdns,
            s.telegram_proxy_username or None,
            s.telegram_proxy_password or None,
        )
    # http
    log.info(
        "Telethon proxy: HTTP %s:%d",
        s.telegram_proxy_host, s.telegram_proxy_port,
    )
    return ("http", s.telegram_proxy_host, s.telegram_proxy_port)


def create_raw_client() -> TelegramClient:
    """
    Construct (but do NOT start) a Telethon client.

    The caller is responsible for `await client.start()` and for wrapping
    the client in `ReadOnlyClient`.
    """
    s = get_settings()
    os.makedirs(_SESSION_DIR, exist_ok=True)
    session_path = os.path.join(_SESSION_DIR, s.telegram_session_name)
    log.info("Building Telethon client (session=%s)", session_path)
    return TelegramClient(
        session=session_path,
        api_id=s.telegram_api_id,
        api_hash=s.telegram_api_hash,
        proxy=_build_proxy(),
        # device params — purely cosmetic, helps avoid automated-detection flags
        device_model="OrganizerBot",
        system_version="1.0",
        app_version="0.1.0",
        lang_code="en",
        system_lang_code="en",
    )