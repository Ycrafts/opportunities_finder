"""
Generate a Pyrogram session string for Telegram ingestion.

Usage:
  1) Put these in your .env (NOT committed):
       PYROGRAM_API_ID=...
       PYROGRAM_API_HASH=...

  2) Run:
       python ingestion/generate_pyrogram_session.py

  3) Follow the prompts (phone number, code, optional 2FA password).
  4) Copy the printed session string into .env:
       PYROGRAM_SESSION_STRING=...

Security:
  - Treat the session string like a password. Do NOT share it.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    api_id = os.getenv("PYROGRAM_API_ID")
    api_hash = os.getenv("PYROGRAM_API_HASH")
    if not api_id or not api_hash:
        raise SystemExit(
            "Missing PYROGRAM_API_ID/PYROGRAM_API_HASH in environment (.env)."
        )

    try:
        api_id_int = int(api_id)
    except ValueError as e:
        raise SystemExit("PYROGRAM_API_ID must be an integer.") from e

    # Import lazily so this script can fail gracefully if pyrogram isn't installed yet.
    try:
        from pyrogram import Client  # type: ignore
    except Exception as e:
        raise SystemExit(
            "pyrogram is not installed. Install it first, e.g.: pip install pyrogram"
        ) from e

    app = Client(
        name="opportunity_finder_session",
        api_id=api_id_int,
        api_hash=api_hash,
        in_memory=True,  # do not create a .session file
    )

    # This will prompt for phone/code/2FA in the terminal.
    with app:
        session_string = app.export_session_string()
        print("\nPYROGRAM_SESSION_STRING=" + session_string + "\n")


if __name__ == "__main__":
    main()


