from __future__ import annotations

import logging
from html import escape
from typing import Any
from urllib.parse import parse_qs, urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.auth import TokenManager, login
from bot.client import get_api_client, get_api_headers
from bot.config import get_settings
from bot.storage import TokenStore

logging.basicConfig(level=logging.INFO)
token_store = TokenStore()
LOGIN_EMAIL, LOGIN_PASSWORD = range(2)


def format_opportunity(opportunity: dict[str, Any]) -> str:
    title = escape(opportunity.get("title") or "Untitled")
    organization = escape(opportunity.get("organization") or "Unknown org")
    source_url = escape(opportunity.get("source_url") or "")
    description = (opportunity.get("description_en") or "").strip()
    location = opportunity.get("location") or {}
    location_name = escape(location.get("name") or "")
    if description:
        description = description.replace("\n", " ")
        if len(description) > 160:
            description = f"{description[:157]}..."
        description = escape(description)

    lines = [f"<b>{title}</b>", f"{organization}"]
    if location_name:
        lines.append(f"Location: {location_name}")
    if description:
        lines.append(description)
    if source_url:
        lines.append(f"Apply: {source_url}")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await send_menu(update, "Welcome to Opportunity Finder. Use the menu below.")


async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    await update.message.reply_text("Send your email address:")
    return LOGIN_EMAIL


async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    context.user_data["login_email"] = update.message.text.strip()
    await update.message.reply_text("Now send your password:")
    return LOGIN_PASSWORD


async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    email = context.user_data.get("login_email", "")
    password = update.message.text
    settings = get_settings()

    try:
        tokens = await login(settings.api_base_url, email, password)
    except Exception:
        await update.message.reply_text("Login failed. Check your credentials.")
        return ConversationHandler.END

    token_store.set_refresh_token(update.effective_user.id, tokens.refresh)
    await send_menu(update, "Login successful. Use the menu to continue.")
    return ConversationHandler.END


async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("Login canceled.")
    return ConversationHandler.END


async def menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    await update.callback_query.answer()
    action = update.callback_query.data
    if action == "menu_login":
        await update.callback_query.message.reply_text("Send /login to start.")
    elif action == "menu_opportunities":
        await list_opportunities(update, context)
    elif action == "menu_matches":
        await list_matches(update, context)


async def menu_text_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    selection = update.message.text or ""
    if selection == "Opportunities":
        await list_opportunities(update, context)
    elif selection == "Matches":
        await list_matches(update, context)


async def opportunities_page_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    await update.callback_query.answer()
    data = update.callback_query.data or ""
    if not data.startswith("opps_page:"):
        return
    page = int(data.split(":", 1)[1])
    await list_opportunities(update, context, page=page)


async def list_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    settings = get_settings()
    user = update.effective_user
    if not user:
        return
    refresh_token = token_store.get_refresh_token(user.id)
    if not refresh_token:
        await _reply(update, "Please /login first to link your account.")
        return
    token_manager = TokenManager(
        base_url=settings.api_base_url,
        email="",
        password="",
        refresh_token=refresh_token,
    )
    headers = await get_api_headers(token_manager)
    async with get_api_client(settings.api_base_url, headers) as client:
        response = await client.get("/api/opportunities/", params={"page": page})
    if response.status_code != 200:
        await _reply(update, "Unable to fetch opportunities right now.")
        return

    payload = response.json()
    results = payload.get("results", payload)
    if not results:
        await _reply(update, "No opportunities found.")
        return

    message = "\n\n".join(format_opportunity(item) for item in results[:5])
    next_page = _get_page_number(payload.get("next"))
    prev_page = _get_page_number(payload.get("previous"))
    keyboard = []
    row = []
    if prev_page:
        row.append(InlineKeyboardButton("Prev", callback_data=f"opps_page:{prev_page}"))
    if next_page:
        row.append(InlineKeyboardButton("Next", callback_data=f"opps_page:{next_page}"))
    if row:
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await _reply_chunks(update, message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def search_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await _reply(update, "Usage: /search <keyword>")
        return

    settings = get_settings()
    user = update.effective_user
    if not user:
        return
    refresh_token = token_store.get_refresh_token(user.id)
    if not refresh_token:
        await _reply(update, "Please /login first to link your account.")
        return
    token_manager = TokenManager(
        base_url=settings.api_base_url,
        email="",
        password="",
        refresh_token=refresh_token,
    )
    headers = await get_api_headers(token_manager)
    async with get_api_client(settings.api_base_url, headers) as client:
        response = await client.get("/api/opportunities/", params={"q": query, "page": 1})
    if response.status_code != 200:
        await _reply(update, "Unable to search right now.")
        return

    payload = response.json()
    results = payload.get("results", payload)
    if not results:
        await _reply(update, "No matches found.")
        return

    message = "\n\n".join(format_opportunity(item) for item in results[:5])
    await _reply_chunks(update, message, parse_mode=ParseMode.HTML)


async def list_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings()
    user = update.effective_user
    if not user:
        return
    refresh_token = token_store.get_refresh_token(user.id)
    if not refresh_token:
        await _reply(update, "Please /login first to link your account.")
        return
    token_manager = TokenManager(
        base_url=settings.api_base_url,
        email="",
        password="",
        refresh_token=refresh_token,
    )
    headers = await get_api_headers(token_manager)
    async with get_api_client(settings.api_base_url, headers) as client:
        response = await client.get("/api/matches/", params={"page": 1})
    if response.status_code != 200:
        await _reply(update, "Unable to fetch matches right now.")
        return
    payload = response.json()
    results = payload.get("results", payload)
    if not results:
        await _reply(update, "No matches found.")
        return
    formatted = []
    for item in results[:5]:
        opportunity = item.get("opportunity") or {}
        title = escape(opportunity.get("title") or "Untitled")
        org = escape(opportunity.get("organization") or "Unknown org")
        score = item.get("match_score")
        source_url = escape(opportunity.get("source_url") or "")
        lines = [f"<b>{title}</b>", org]
        if score is not None:
            lines.append(f"Score: {score}")
        if source_url:
            lines.append(f"Details: {source_url}")
        formatted.append("\n".join(lines))
    await _reply_chunks(update, "\n\n".join(formatted), parse_mode=ParseMode.HTML)


async def _reply(update: Update, text: str, **kwargs: Any) -> None:
    if update.message:
        await update.message.reply_text(text, **kwargs)
        return
    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, **kwargs)


async def _reply_chunks(update: Update, text: str, **kwargs: Any) -> None:
    max_len = 3500
    for i in range(0, len(text), max_len):
        chunk = text[i : i + max_len]
        await _reply(update, chunk, **kwargs)


def _get_page_number(url: str | None) -> int | None:
    if not url:
        return None
    query = parse_qs(urlparse(url).query)
    page_values = query.get("page")
    if not page_values:
        return None
    try:
        return int(page_values[0])
    except ValueError:
        return None


async def send_menu(update: Update, message: str) -> None:
    keyboard = []
    user = update.effective_user
    if not user or not token_store.get_refresh_token(user.id):
        keyboard.append(["Login"])
    keyboard.append(["Opportunities", "Matches"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await _reply(update, message, reply_markup=reply_markup)


def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Set it in .env.")

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_action, pattern="^menu_"))
    application.add_handler(CallbackQueryHandler(opportunities_page_action, pattern="^opps_page:"))
    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("login", login_start),
                MessageHandler(filters.Regex("^Login$"), login_start),
            ],
            states={
                LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
                LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
            },
            fallbacks=[CommandHandler("cancel", login_cancel)],
        )
    )
    application.add_handler(
        MessageHandler(filters.Regex("^(Opportunities|Matches)$"), menu_text_action)
    )
    application.add_handler(CommandHandler("opportunities", list_opportunities))
    application.add_handler(CommandHandler("search", search_opportunities))
    application.add_handler(CommandHandler("matches", list_matches))

    application.run_polling()


if __name__ == "__main__":
    main()
