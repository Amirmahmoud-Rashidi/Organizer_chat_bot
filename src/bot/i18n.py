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
    "menu.delivery_mode": "📤 حالت ارسال",
    "menu.pace": "⏱ سرعت خواندن",
    "menu.language": "🌐 تغییر زبان",
    "menu.cancel": "❌ لغو",

    # --- Read pace ---
    "pace.title": "⏱ سرعت خواندن پیام‌ها",
    "pace.choose": "یک preset انتخاب کن:",
    "pace.current": "سرعت فعلی: **{label}**",
    "pace.custom_label": "✏️ سفارشی (دستی)",
    "pace.custom_desc": "مقادیر دلخواه: `10,1.0,50,5.0` (size,delay,long_size,long_delay)",
    "pace.custom_prompt": "۴ عدد بفرست با کاما: `fast_size,fast_delay,long_size,long_delay`\nمثال: `5,2.0,30,8.0`",
    "pace.custom_invalid": "⚠️ فرمت نامعتبر. مثال: `10,1.0,50,5.0`",
    "pace.custom_saved": "✅ تنظیم سفارشی ذخیره شد: size={0} delay={1}s long_size={2} long_delay={3}s",

    # --- Delivery mode ---
    "delivery.title": "📤 حالت ارسال",
    "delivery.choose": "یکی از حالت‌های زیر رو انتخاب کن:",
    "mode.forward": "↪️ فوروارد پیام‌ها (پیش‌فرض)",
    "mode.forward_desc": "پیام‌های منطبق رو مستقیم به چت مقصد فوروارد می‌کنه (سریع ولی پرریسک).",
    "mode.digest": "📋 ارسال خلاصه با لینک (امن)",
    "mode.digest_desc": "یک پیام خلاصه شامل لینک + متن کوتاه هر پیام منطبق می‌فرسته (بدون ریسک ban).",
    "mode.current": "حالت فعلی: **{mode}**",
    "mode.forward_fa": "فوروارد",
    "mode.digest_fa": "خلاصه",

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
    "run.starting_slow": "⏳ در حال خواندن آرام پیام‌ها و تحلیل…",
    "run.no_chat": "⚠️ اول یک چت انتخاب کن.",
    "run.no_window": "⚠️ اول پنجره زمانی تنظیم کن.",
    "run.no_prompt": "⚠️ اول پرامپت تنظیم کن.",
    "run.no_destination": "⚠️ اول مقصد فوروارد تنظیم کن.",
    "run.done_zero": "ℹ️ هیچ پیام منطبقی پیدا نشد.",
    "run.done_n_forward": "✅ {n} پیام به مقصد فوروارد شد.",
    "run.done_n_digest": "✅ خلاصه {n} پیام منطبق به مقصد ارسال شد.",
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
    "menu.delivery_mode": "📤 Delivery mode",
    "menu.pace": "⏱ Read pace",
    "menu.language": "🌐 Change language",
    "menu.cancel": "❌ Cancel",

    # --- Read pace ---
    "pace.title": "⏱ Read pace",
    "pace.choose": "Pick a preset:",
    "pace.current": "Current pace: **{label}**",
    "pace.custom_label": "✏️ Custom",
    "pace.custom_desc": "Custom values: `10,1.0,50,5.0` (size,delay,long_size,long_delay)",
    "pace.custom_prompt": "Send 4 numbers separated by commas: `fast_size,fast_delay,long_size,long_delay`\nExample: `5,2.0,30,8.0`",
    "pace.custom_invalid": "⚠️ Invalid format. Example: `10,1.0,50,5.0`",
    "pace.custom_saved": "✅ Custom pace saved: size={0} delay={1}s long_size={2} long_delay={3}s",

    # --- Delivery mode ---
    "delivery.title": "📤 Delivery mode",
    "delivery.choose": "Pick a delivery mode:",
    "mode.forward": "↪️ Forward messages (default)",
    "mode.forward_desc": "Directly forwards matching messages to the destination chat (fast but higher risk).",
    "mode.digest": "📋 Send digest with links (safe)",
    "mode.digest_desc": "Sends one summary message with links + excerpts (no ban risk).",
    "mode.current": "Current mode: **{mode}**",
    "mode.forward_fa": "Forward",
    "mode.digest_fa": "Digest",

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
    "run.starting_slow": "⏳ Slow-reading messages and analyzing…",
    "run.no_chat": "⚠️ Select a chat first.",
    "run.no_window": "⚠️ Set a time window first.",
    "run.no_prompt": "⚠️ Set a prompt first.",
    "run.no_destination": "⚠️ Set a forward destination first.",
    "run.done_zero": "ℹ️ No matching messages found.",
    "run.done_n_forward": "✅ Forwarded {n} message(s) to destination.",
    "run.done_n_digest": "✅ Sent digest with {n} match(es) to destination.",
    "run.error": "❌ Error during run: {err}",

    "auth.denied": "⛔ You are not authorized to use this bot.",

    "cancelled": "🚫 Cancelled.",
}

_TABLE: dict[Lang, dict[str, str]] = {"fa": MESSAGES_FA, "en": MESSAGES_EN}


def t(key: str, lang: Lang = "fa", *args: object, **kwargs: object) -> str:
    """
    Translate `key` to `lang`. Falls back to Persian, then to `key`.

    Supports both styles used across the codebase:
      * `{name}` placeholders -> pass as `**kwargs`
      * `{0} {1} ...` placeholders -> pass as positional `*args`
        (e.g. `t("pace.custom_saved", lang, fast_size, fast_delay, ...)`)
    """
    table = _TABLE.get(lang, MESSAGES_FA)
    template = table.get(key) or MESSAGES_FA.get(key) or key
    try:
        return template.format(*args, **kwargs)
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
