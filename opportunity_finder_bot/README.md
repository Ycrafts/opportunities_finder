# Opportunity Finder Telegram Bot (Scaffold)

Minimal scaffold for a Telegram bot frontend. No business logic implemented yet.

## Setup
1. Copy `.env.example` to `.env` and add your Telegram bot token.
2. Create a virtualenv and install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python -m bot.main
   ```

## Bot commands
- `/login <email> <password>` link your account (stores refresh token locally).
- `/opportunities` list latest opportunities.
- `/search <keyword>` search opportunities.

The bot stores refresh tokens in `data/tokens.json`.
