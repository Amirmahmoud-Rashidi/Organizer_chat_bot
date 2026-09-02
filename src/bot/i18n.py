# filepath: src/bot/i18n.py
"""
Minimal i18n for two languages: Persian (fa) and English (en).

We use simple dictionaries + a `t()` function. For a 2-language bot this
is much more maintainable than gettext-style workflows. Every user-facing
string in the bot MUST be defined here.
"""

from __future__ import annotations

from typing import Literal

Lang = Literal["fa", "en"]

# --------------------------------------------------------------------------
# Persian strings (default)
# --------------------------------------------------------------------------
MESSAGES_FA: dict[str, str] = {
    # --- General ---
    "welcome": (
        "👋 سلام! به ربات سازماندهی چت خوش اومدی.\n\n"
        "این ربات چت‌های انتخابی تو رو با یک پرامپت دلخواه بررسی می‌کنه و "
        "پیام‌های منطبق رو به چت مقصدت فوروارد می‌کنه.\n\n"
        "از منوی زیر یک گزینه رو انتخاب کن:"
    ),
    "menu.title": "🏠 منوی اصلی",
    "menu.select_chat": "💬 انتخاب چت",
    "menu.select_window": "⏱ پنجره زمانی",
    "menu.set_prompt": "📝 پرامپت جدید",
    "menu.recent_prompts": "🕘 پرامپت‌های اخیر",
    "menu.set_destination": "📨 مقصد فوروارد",
    "menu.run": "▶️ اجرا",
    "menu.language": "🌐 تغییر زبان",
    "menu.cancel": "❌ لغو",

    # --- Language ---
    "lang.choose": "🌐 زبان رو انتخاب کن:",
    "lang.changed_fa": "✅ زبان به فارسی تغییر کرد.",
    "lang.changed_en": "✅ Language switched to English.",
    "lang.invalid": "⚠️ زبان نامعتبر. از `fa` یا `en` استفاده کن.",

    # --- Chat selection ---
    "chat.pick": "💬 یک چت انتخاب کن (یا `/cancel` بزن):",
    "chat.empty": "⚠️ هیچ گفتگویی پیدا نشد.",
    "chat.selected": "✅ چت انتخاب شد: **{title}**",

    # --- Time window ---
    "window.pick": "⏱ پنجره زمانی رو انتخاب کن (یا مقدار دلخواه بفرست مثل `48h`، `10d`):",
    "window.custom_hint": "مثال: `30m`, `2h`, `3d`, `1w`",
    "window.selected": "✅ پنجره زمانی تنظیم شد: **{window}**",
    "window.invalid": "⚠️ فرمت نامعتبر. مثال: `48h`, `7d`, `30m`.",

    # --- Prompt ---
    "prompt.send_new": "📝 پرامپت جدیدت رو بفرست. توضیح بده دنبال چه نوع پیام‌هایی می‌گردی.",
    "prompt.saved": "✅ پرامپت ذخیره شد.",
    "prompt.recent_title": "🕘 ۱۰ پرامپت آخر:",
    "prompt.empty": "⚠️ هنوز پرامپتی ذخیره نشده.",
    "prompt.not_set": "⚠️ هنوز پرامپتی تنظیم نکردی. اول «📝 پرامپت جدید» رو بزن.",

    # --- Destination ---
    "dest.send": "📨 مقصد فوروارد رو بفرست (`@channel_username` یا chat ID).",
    "dest.saved": "✅ مقصد فوروارد تنظیم شد: `{dest}`",
    "dest.invalid": "⚠️ مقصد نامعتبر.",

    # --- Run ---
    "run.starting": "⏳ در حال تحلیل…",
    "run.no_chat": "⚠️ اول یک چت انتخاب کن.",
    "run.no_window": "⚠️ اول پنجره زمانی تنظیم کن.",
    "run.no_prompt": "⚠️ اول پرامپت تنظیم کن.",
    "run.no_destination": "⚠️ اول مقصد فوروارد تنظیم کن.",
    "run.done_zero": "ℹ️ هیچ پیام منطبقی پیدا نشد.",
    "run.done_n": "✅ {n} پیام به مقصد فوروارد شد.",
    "run.error": "❌ خطا در اجرا: {err}",

    # --- Unauthorized ---
    "auth.denied": "⛔ شما مجاز به استفاده از این ربات نیستید.",

    # --- Misc ---
    "cancelled": "🚫 لغو شد.",
}

# --------------------------------------------------------------------------
# English strings
# --------------------------------------------------------------------------
MESSAGES_EN: dict[str, str] = {
    "welcome": (
        "👋 Hi! Welcome to the Chat Organizer bot.\n\n"
        "This bot scans your selected chats for messages matching a custom "
        "prompt and forwards the matches to a destination chat.\n\n"
        "Pick an option from the menu below:"
    ),
    "menu.title": "🏠 Main menu",
    "menu.select_chat": "💬 Select chat",
    "menu.select_window": "⏱ Time window",
    "menu.set_prompt": "📝 New prompt",
    "menu.recent_prompts": "🕘 Recent prompts",
    "menu.set_destination": "📨 Forward destination",
    "menu.run": "▶️ Run",
    "menu.language": "🌐 Change language",
    "menu.cancel": "❌ Cancel",

    "lang.choose": "🌐 Choose a language:",
    "lang.changed_fa": "✅ زبان به فارسی تغییر کرد.",
    "lang.changed_en": "✅ Language switched to English.",
    "lang.invalid": "⚠️ Invalid language. Use `fa` or `en`.",

    "chat.pick": "💬 Pick a chat (or send `/cancel`):",
    "chat.empty": "⚠️ No conversations found.",
    "chat.selected": "✅ Chat selected: **{title}**",

    "window.pick": "⏱ Pick a time window (or send a custom value like `48h`, `10d`):",
    "window.custom_hint": "Examples: `30m`, `2h`, `3d`, `1w`",
    "window.selected": "✅ Time window set: **{window}**",
    "window.invalid": "⚠️ Invalid format. Examples: `48h`, `7d`, `30m`.",

    "prompt.send_new": "📝 Send your new prompt. Describe what kind of messages you're looking for.",
    "prompt.saved": "✅ Prompt saved.",
    "prompt.recent_title": "🕘 Recent prompts (last 10):",
    "prompt.empty": "⚠️ No prompts saved yet.",
    "prompt.not_set": "⚠️ No prompt set yet. Tap '📝 New prompt' first.",

    "dest.send": "📨 Send the forward destination (`@channel_username` or chat ID).",
    "dest.saved": "✅ Forward destination set: `{dest}`",
    "dest.invalid": "⚠️ Invalid destination.",

    "run.starting": "⏳ Analyzing…",
    "run.no_chat": "⚠️ Select a chat first.",
    "run.no_window": "⚠️ Set a time window first.",
    "run.no_prompt": "⚠️ Set a prompt first.",
    "run.no_destination": "⚠️ Set a forward destination first.",
    "run.done_zero": "ℹ️ No matching messages found.",
    "run.done_n": "✅ Forwarded {n} message(s) to destination.",
    "run.error": "❌ Error during run: {err}",

    "auth.denied": "⛔ You are not authorized to use this bot.",

    "cancelled": "🚫 Cancelled.",
}

_TABLE: dict[Lang, dict[str, str]] = {"fa": MESSAGES_FA, "en": MESSAGES_EN}


def t(key: str, lang: Lang = "fa", **kwargs: object) -> str:
    """
    Translate `key` to `lang`. Falls back to Persian, then to `key`.

    `kwargs` are substituted via `.format(**kwargs)` (only `{name}` style).
    """
    table = _TABLE.get(lang, MESSAGES_FA)
    template = table.get(key) or MESSAGES_FA.get(key) or key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def parse_window(spec: str) -> int | None:
    """
    Parse a window spec like '30m', '2h', '3d', '1w' into total minutes.

    Returns None on invalid input.
    """
    spec = spec.strip().lower()
    if not spec:
        return None
    unit = spec[-1]
    body = spec[:-1]
    try:
        n = int(body)
    except ValueError:
        return None
    if n <= 0:
        return None
    if unit == "m":
        return n
    if unit == "h":
        return n * 60
    if unit == "d":
        return n * 60 * 24
    if unit == "w":
        return n * 60 * 24 * 7
    return None


def format_window(minutes: int) -> str:
    """Format minutes back into a human-readable spec for display."""
    if minutes < 60:
        return f"{minutes}m"
    if minutes < 60 * 24:
        h = minutes // 60
        return f"{h}h"
    if minutes < 60 * 24 * 7:
        d = minutes // (60 * 24)
        return f"{d}d"
    w = minutes // (60 * 24 * 7)
    return f"{w}w"