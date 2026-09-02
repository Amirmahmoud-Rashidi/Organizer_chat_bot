"""Userbot layer — Telethon client, read-only wrapper, reader, forwarder."""
from src.userbot.client import create_raw_client
from src.userbot.forwarder import forward_messages
from src.userbot.reader import FetchedMessage, fetch_messages, list_dialogs
from src.userbot.summarizer import build_digest, make_message_link, send_digest
from src.userbot.wrapper import ReadOnlyClient

__all__ = [
    "ReadOnlyClient",
    "create_raw_client",
    "FetchedMessage",
    "fetch_messages",
    "list_dialogs",
    "forward_messages",
    "build_digest",
    "make_message_link",
    "send_digest",
]