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
from src.userbot.forwarder import forward_messages as do_forward
from src.userbot.reader import fetch_messages, list_dialogs
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
            [InlineKeyboardButton(t("menu.run", lang), callback_data="menu:run")],
            [
                InlineKeyboardButton(t("menu.language", lang), callback_data="menu:lang"),
                InlineKeyboardButton(t("menu.cancel", lang), callback_data="menu:cancel"),
            ],
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

    await q.edit_message_text(t("run.starting", lang))

    client: ReadOnlyClient = context.bot_data["userbot"]
    analyzer: AIAnalyzer = context.bot_data["analyzer"]
    settings = get_settings()

    since = datetime.now(timezone.utc) - timedelta(minutes=state.window_minutes)
    try:
        msgs = await fetch_messages(
            client,
            entity=state.chat_id,
            since=since,
            max_messages=settings.max_messages_per_run,
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
        ids = await analyzer.analyze(msgs, state.prompt)
    except Exception as exc:
        log.exception("AI analyze failed")
        await q.edit_message_text(
            t("run.error", lang, err=str(exc)),
            reply_markup=main_menu_kb(lang),
        )
        return

    if not ids:
        await q.edit_message_text(t("run.done_zero", lang), reply_markup=main_menu_kb(lang))
        return

    try:
        sent = await do_forward(
            client,
            destination=destination,
            source_entity=state.chat_id,
            message_ids=ids,
        )
    except Exception as exc:
        log.exception("forward failed")
        await q.edit_message_text(
            t("run.error", lang, err=str(exc)),
            reply_markup=main_menu_kb(lang),
        )
        return

    await q.edit_message_text(
        t("run.done_n", lang, n=len(sent)),
        reply_markup=main_menu_kb(lang),
    )