# filepath: src/bot/handlers.py
"""
Telegram Bot handlers (the user-facing interface).

We use python-telegram-bot v21's async API. The handlers are intentionally
simple — they manipulate `UserState` and delegate heavy lifting (Telethon,
AI) to the other layers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.ai.analyzer import AIAnalyzer
from src.bot.auth import authorized
from src.bot.i18n import Lang, format_window, parse_window, t
from src.bot.prompt_history import load_recent_prompts, save_prompt
from src.bot.state import store
from src.config import get_settings
from src.userbot.reader import FetchedMessage, fetch_messages, list_dialogs
from src.userbot.wrapper import ReadOnlyClient

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Keyboard builders
# --------------------------------------------------------------------------

def main_menu_kb(lang: Lang) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("menu.select_chat", lang), callback_data="menu:chat")],
            [InlineKeyboardButton(t("menu.select_window", lang), callback_data="menu:window")],
            [
                InlineKeyboardButton(t("menu.set_prompt", lang), callback_data="menu:prompt"),
                InlineKeyboardButton(t("menu.recent_prompts", lang), callback_data="menu:recent"),
            ],
            [InlineKeyboardButton(t("menu.set_destination", lang), callback_data="menu:dest")],
            [InlineKeyboardButton(t("menu.delivery_mode", lang), callback_data="menu:mode")],
            [InlineKeyboardButton(t("menu.pace", lang), callback_data="menu:pace")],
            [InlineKeyboardButton(t("menu.run", lang), callback_data="menu:run")],
            [
                InlineKeyboardButton(t("menu.language", lang), callback_data="menu:lang"),
                InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel"),
            ],
        ]
    )


def pace_kb(lang: Lang, current: str) -> InlineKeyboardMarkup:
    """Inline keyboard for picking a read-pace preset (plus custom)."""
    from src.bot.presets import all_presets, get_preset

    rows: list[list[InlineKeyboardButton]] = []
    for p in all_presets():
        prefix = "✓ " if current == p.name_preset else ""
        label = prefix + (p.label_fa if lang == "fa" else p.label_en)
        rows.append([InlineKeyboardButton(label, callback_data=f"pace:set:{p.name_preset}")])

    # Custom — current row shows the active custom values if applicable.
    custom_label = ("✓ " if current == "custom" else "") + t("pace.custom_label", lang)
    rows.append([InlineKeyboardButton(custom_label, callback_data="pace:custom")])
    rows.append([InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel")])
    return InlineKeyboardMarkup(rows)


def delivery_mode_kb(lang: Lang, current: str) -> InlineKeyboardMarkup:
    """Inline keyboard for picking forward vs digest mode."""
    label_forward = ("✓ " if current == "forward" else "") + t("mode.forward", lang)
    label_digest = ("✓ " if current == "digest" else "") + t("mode.digest", lang)
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(label_forward, callback_data="mode:set:forward")],
            [InlineKeyboardButton(label_digest, callback_data="mode:set:digest")],
            [InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel")],
        ]
    )


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("\U0001f1ee\U0001f1f7 \u0641\u0627\u0631\u0633\u06cc", callback_data="lang:fa"),
                InlineKeyboardButton("\U0001f1ec\U0001f1e7 English", callback_data="lang:en"),
            ]
        ]
    )


def window_kb(lang: Lang) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("1h", callback_data="win:60"),
                InlineKeyboardButton("6h", callback_data="win:360"),
                InlineKeyboardButton("24h", callback_data="win:1440"),
            ],
            [
                InlineKeyboardButton("3d", callback_data="win:4320"),
                InlineKeyboardButton("7d", callback_data="win:10080"),
                InlineKeyboardButton("30d", callback_data="win:43200"),
            ],
            [InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel")],
        ]
    )


def chat_picker_kb(dialogs: list[dict[str, Any]], lang: Lang) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for d in dialogs:
        title = d["title"]
        if len(title) > 30:
            title = title[:27] + "\u2026"
        eid = d["id"]
        if eid is None:
            continue
        row.append(InlineKeyboardButton(title, callback_data=f"chat:{eid}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel")])
    return InlineKeyboardMarkup(rows)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

@authorized
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    state = store.get(user_id)
    state.lang = state.lang or get_settings().default_language  # type: ignore[assignment]
    await update.effective_message.reply_text(  # type: ignore[union-attr]
        t("welcome", state.lang),
        reply_markup=main_menu_kb(state.lang),
    )


@authorized
async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    state = store.get(user_id)
    args = context.args or []

    if not args:
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t("lang.choose", state.lang),
            reply_markup=lang_kb(),
        )
        return

    candidate = args[0].lower()
    if candidate not in ("fa", "en"):
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t("lang.invalid", state.lang),
        )
        return
    state.lang = candidate  # type: ignore[assignment]
    await update.effective_message.reply_text(  # type: ignore[union-attr]
        t(f"lang.changed_{candidate}", state.lang),
        reply_markup=main_menu_kb(state.lang),
    )


# --------------------------------------------------------------------------
# Callback dispatcher
# --------------------------------------------------------------------------

@authorized
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route inline-keyboard presses."""
    q = update.callback_query
    if q is None:
        return
    await q.answer()
    data = q.data or ""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    state = store.get(user_id)
    lang = state.lang
    client: ReadOnlyClient = context.bot_data["userbot"]

    if data == "menu:cancel":
        await q.edit_message_text(t("cancelled", lang), reply_markup=main_menu_kb(lang))
        store.reset(user_id)
        return

    if data == "menu:chat":
        dialogs = await list_dialogs(client, limit=80)
        if not dialogs:
            await q.edit_message_text(t("chat.empty", lang), reply_markup=main_menu_kb(lang))
            return
        await q.edit_message_text(
            t("chat.pick", lang),
            reply_markup=chat_picker_kb(dialogs, lang),
        )
        return

    if data == "menu:window":
        await q.edit_message_text(
            f"{t('window.pick', lang)}\n\n_{t('window.custom_hint', lang)}_",
            reply_markup=window_kb(lang),
        )
        state.waiting_for = "window_custom"
        return

    if data.startswith("win:"):
        minutes = int(data.split(":", 1)[1])
        state.window_minutes = minutes
        state.waiting_for = None
        await q.edit_message_text(
            t("window.selected", lang, window=format_window(minutes)),
            reply_markup=main_menu_kb(lang),
        )
        return

    if data == "menu:prompt":
        state.waiting_for = "prompt"
        await q.edit_message_text(t("prompt.send_new", lang), reply_markup=main_menu_kb(lang))
        return

    if data == "menu:recent":
        prompts = await load_recent_prompts(client)
        if not prompts:
            await q.edit_message_text(t("prompt.empty", lang), reply_markup=main_menu_kb(lang))
            return
        rows: list[list[InlineKeyboardButton]] = []
        for p in prompts:
            label = p.text.replace("\n", " ")
            if len(label) > 40:
                label = label[:37] + "\u2026"
            rows.append([InlineKeyboardButton(label, callback_data=f"recent:{p.msg_id}")])
        rows.append([InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel")])
        await q.edit_message_text(
            t("prompt.recent_title", lang),
            reply_markup=InlineKeyboardMarkup(rows),
        )
        return

    if data == "menu:dest":
        state.waiting_for = "destination"
        await q.edit_message_text(
            f"{t('dest.send', lang)}\n\n"
            f"_(default: `{get_settings().forward_destination}`)_",
            reply_markup=main_menu_kb(lang),
        )
        return

    if data == "menu:mode":
        await q.edit_message_text(
            f"{t('delivery.title', lang)}\n\n"
            f"_{t('mode.forward_desc', lang)}_\n\n"
            f"_{t('mode.digest_desc', lang)}_\n\n"
            f"{t('mode.current', lang, mode=t(f'mode.{state.delivery_mode}_fa', lang))}",
            reply_markup=delivery_mode_kb(lang, state.delivery_mode),
        )
        return

    if data == "menu:pace":
        from src.bot.presets import get_preset

        current = get_preset(state.pace_preset)
        current_label = (
            current.label_fa if state.pace_preset != "custom" else t("pace.custom_label", lang)
        )
        if lang == "fa":
            current_desc = current.desc_fa if state.pace_preset != "custom" else t("pace.custom_desc", lang)
        else:
            current_desc = current.desc_en if state.pace_preset != "custom" else t("pace.custom_desc", lang)
        await q.edit_message_text(
            f"{t('pace.title', lang)}\n\n"
            f"_{current_desc}_\n\n"
            f"{t('pace.current', lang, label=current_label)}",
            reply_markup=pace_kb(lang, state.pace_preset),
        )
        return

    if data.startswith("pace:set:"):
        from src.bot.presets import get_preset

        name = data.split(":", 2)[2]
        if name in ("safe", "normal", "fast"):
            state.pace_preset = name  # type: ignore[assignment]
            cfg = get_preset(name)
            label = cfg.label_fa if lang == "fa" else cfg.label_en
            await q.edit_message_text(
                t("pace.current", lang, label=label),
                reply_markup=main_menu_kb(lang),
            )
        return

    if data == "pace:custom":
        state.waiting_for = "pace_custom"
        state.pace_preset = "custom"
        await q.edit_message_text(
            t("pace.custom_prompt", lang),
            reply_markup=main_menu_kb(lang),
        )
        return

    if data.startswith("mode:set:"):
        new_mode = data.split(":", 2)[2]
        if new_mode in ("forward", "digest"):
            state.delivery_mode = new_mode  # type: ignore[assignment]
            await q.edit_message_text(
                t("mode.current", lang, mode=t(f"mode.{new_mode}_fa", lang)),
                reply_markup=main_menu_kb(lang),
            )
        return

    if data == "menu:lang":
        await q.edit_message_text(t("lang.choose", lang), reply_markup=lang_kb())
        return

    if data.startswith("lang:"):
        new_lang = data.split(":", 1)[1]
        if new_lang in ("fa", "en"):
            state.lang = new_lang  # type: ignore[assignment]
            await q.edit_message_text(
                t(f"lang.changed_{new_lang}", state.lang),
                reply_markup=main_menu_kb(state.lang),
            )
        return

    if data.startswith("chat:"):
        chat_id = int(data.split(":", 1)[1])
        try:
            entity = await client.get_entity(chat_id)
        except Exception as exc:
            log.warning("get_entity failed for %s: %s", chat_id, exc)
            await q.edit_message_text(t("chat.empty", lang), reply_markup=main_menu_kb(lang))
            return
        state.chat_id = chat_id
        title = getattr(entity, "title", None) or getattr(entity, "first_name", None) or str(chat_id)
        state.chat_title = str(title)
        await q.edit_message_text(
            t("chat.selected", lang, title=state.chat_title),
            reply_markup=main_menu_kb(lang),
        )
        return

    if data.startswith("recent:"):
        msg_id = int(data.split(":", 1)[1])
        prompts = await load_recent_prompts(client)
        match = next((p for p in prompts if p.msg_id == msg_id), None)
        if match is None:
            await q.edit_message_text(t("prompt.empty", lang), reply_markup=main_menu_kb(lang))
            return
        state.prompt = match.text
        snippet = match.text[:200].replace("`", "'")
        await q.edit_message_text(
            f"{t('prompt.saved', lang)}\n\n`{snippet}`",
            reply_markup=main_menu_kb(lang),
        )
        return

    if data == "menu:run":
        await _run_pipeline(q, context, lang, user_id)
        return


# --------------------------------------------------------------------------
# Free-text handler (for prompt / destination / custom window)
# --------------------------------------------------------------------------

@authorized
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    state = store.get(user_id)
    lang = state.lang
    text = (update.effective_message.text or "").strip()  # type: ignore[union-attr]

    if text == "/cancel":
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t("cancelled", lang),
            reply_markup=main_menu_kb(lang),
        )
        store.reset(user_id)
        return

    if state.waiting_for == "prompt":
        if not text:
            return
        state.prompt = text
        client: ReadOnlyClient = context.bot_data["userbot"]
        await save_prompt(client, text)
        state.waiting_for = None
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t("prompt.saved", lang),
            reply_markup=main_menu_kb(lang),
        )
        return

    if state.waiting_for == "destination":
        state.destination = text
        state.waiting_for = None
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t("dest.saved", lang, dest=text),
            reply_markup=main_menu_kb(lang),
        )
        return

    if state.waiting_for == "window_custom":
        minutes = parse_window(text)
        if minutes is None:
            await update.effective_message.reply_text(  # type: ignore[union-attr]
                t("window.invalid", lang),
            )
            return
        state.window_minutes = minutes
        state.waiting_for = None
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t("window.selected", lang, window=format_window(minutes)),
            reply_markup=main_menu_kb(lang),
        )
        return
    if state.waiting_for == "pace_custom":
        try:
            parts = [p.strip() for p in text.split(",")]
            if len(parts) != 4:
                raise ValueError
            fast_size = int(parts[0])
            fast_delay = float(parts[1])
            long_size = int(parts[2])
            long_delay = float(parts[3])
            if fast_size < 1 or long_size < 1 or fast_delay < 0 or long_delay < 0:
                raise ValueError
        except (ValueError, IndexError):
            await update.effective_message.reply_text(  # type: ignore[union-attr]
                t("pace.custom_invalid", lang),
            )
            return
        state.custom_fast_batch_size = fast_size
        state.custom_fast_batch_delay = fast_delay
        state.custom_batch_size = long_size
        state.custom_long_pause_delay = long_delay
        state.pace_preset = "custom"
        state.waiting_for = None
        await update.effective_message.reply_text(  # type: ignore[union-attr]
            t(
                "pace.custom_saved",
                lang,
                fast_size, fast_delay, long_size, long_delay,
            ),
            reply_markup=main_menu_kb(lang),
        )
        return
    # Default \u2014 re-show menu.
    await update.effective_message.reply_text(  # type: ignore[union-attr]
        t("menu.title", lang),
        reply_markup=main_menu_kb(lang),
    )


# --------------------------------------------------------------------------
# Pipeline runner
# --------------------------------------------------------------------------

async def _run_pipeline(
    q: Any, context: ContextTypes.DEFAULT_TYPE, lang: Lang, user_id: int
) -> None:
    state = store.get(user_id)
    if state.chat_id is None:
        await q.edit_message_text(t("run.no_chat", lang), reply_markup=main_menu_kb(lang))
        return
    if state.window_minutes is None:
        await q.edit_message_text(t("run.no_window", lang), reply_markup=main_menu_kb(lang))
        return
    if not state.prompt:
        await q.edit_message_text(t("run.no_prompt", lang), reply_markup=main_menu_kb(lang))
        return
    destination = state.destination or get_settings().forward_destination
    if not destination:
        await q.edit_message_text(t("run.no_destination", lang), reply_markup=main_menu_kb(lang))
        return

    starting_msg = (
        t("run.starting_slow", lang)
        if state.delivery_mode == "digest"
        else t("run.starting", lang)
    )
    await q.edit_message_text(starting_msg)

    client: ReadOnlyClient = context.bot_data["userbot"]
    analyzer: AIAnalyzer = context.bot_data["analyzer"]
    settings = get_settings()

    since = datetime.now(timezone.utc) - timedelta(minutes=state.window_minutes)

    # Resolve pacing: preset from UI > custom values > .env defaults
    from src.bot.presets import get_preset

    if state.pace_preset == "custom":
        slow_read = settings.slow_read_enabled
        fast_batch_size = state.custom_fast_batch_size or settings.fast_batch_size
        fast_batch_delay = state.custom_fast_batch_delay or settings.fast_batch_delay
        batch_size = state.custom_batch_size or settings.batch_size
        long_pause_delay = state.custom_long_pause_delay or settings.long_pause_delay
    else:
        cfg = get_preset(state.pace_preset)
        slow_read = cfg.slow_read_enabled
        fast_batch_size = cfg.fast_batch_size
        fast_batch_delay = cfg.fast_batch_delay
        batch_size = cfg.batch_size
        long_pause_delay = cfg.long_pause_delay

    try:
        msgs = await fetch_messages(
            client,
            entity=state.chat_id,
            since=since,
            max_messages=settings.max_messages_per_run,
            # Slow-read pacing from the active preset (or custom / .env fallback).
            slow_read=slow_read,
            fast_batch_size=fast_batch_size,
            fast_batch_delay=fast_batch_delay,
            batch_size=batch_size,
            long_pause_delay=long_pause_delay,
        )
    except Exception as exc:
        log.exception("fetch_messages failed")
        await q.edit_message_text(
            t("run.error", lang, err=str(exc)),
            reply_markup=main_menu_kb(lang),
        )
        return

    if not msgs:
        await q.edit_message_text(t("run.done_zero", lang), reply_markup=main_menu_kb(lang))
        return

    try:
        matches = await analyzer.analyze(msgs, state.prompt)
    except Exception as exc:
        log.exception("AI analyze failed")
        await q.edit_message_text(
            t("run.error", lang, err=str(exc)),
            reply_markup=main_menu_kb(lang),
        )
        return

    if not matches:
        await q.edit_message_text(t("run.done_zero", lang), reply_markup=main_menu_kb(lang))
        return

    # Build (FetchedMessage, reason) tuples in the original message order.
    ordered: list[tuple[FetchedMessage, str]] = [
        (m, matches.get(m.id, "")) for m in msgs if m.id in matches
    ]

    # ---- Delivery: digest (default, safe) or forward ----
    try:
        if state.delivery_mode == "digest":
            from src.userbot.summarizer import build_digest, send_digest

            entity = await client.get_entity(state.chat_id)
            text = build_digest(entity, ordered, prompt=state.prompt)
            await send_digest(client, destination=destination, text=text)
            await q.edit_message_text(
                t("run.done_n_digest", lang, n=len(ordered)),
                reply_markup=main_menu_kb(lang),
            )
        else:
            from src.userbot.forwarder import forward_messages as do_forward

            sent = await do_forward(
                client,
                destination=destination,
                source_entity=state.chat_id,
                message_ids=[m.id for m, _ in ordered],
            )
            await q.edit_message_text(
                t("run.done_n_forward", lang, n=len(sent)),
                reply_markup=main_menu_kb(lang),
            )
    except Exception as exc:
        log.exception("delivery failed")
        await q.edit_message_text(
            t("run.error", lang, err=str(exc)),
            reply_markup=main_menu_kb(lang),
        )
        return