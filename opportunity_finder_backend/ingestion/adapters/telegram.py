from __future__ import annotations

import asyncio
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone

from opportunities.models import Source

from .base import BaseAdapter, RawItem


class TelegramAdapter(BaseAdapter):
    """
    Telegram ingestion via Pyrogram (MTProto).

    Expects:
      - source.source_type == TELEGRAM
      - source.identifier contains channel username/link/id
    """

    def __init__(self):
        if not settings.PYROGRAM_API_ID or not settings.PYROGRAM_API_HASH:
            raise RuntimeError("Missing PYROGRAM_API_ID/PYROGRAM_API_HASH in settings/env.")
        if not getattr(settings, "PYROGRAM_SESSION_STRING", None):
            raise RuntimeError("Missing PYROGRAM_SESSION_STRING in settings/env.")

        self.api_id = int(settings.PYROGRAM_API_ID)
        self.api_hash = settings.PYROGRAM_API_HASH
        self.session_string = settings.PYROGRAM_SESSION_STRING

    def _as_aware_utc(self, dt: datetime | None) -> datetime | None:
        """
        Pyrogram may return naive datetimes; Django typically uses aware datetimes when USE_TZ=True.
        Normalize everything to aware UTC to avoid comparison errors.
        """
        if dt is None:
            return None
        if timezone.is_aware(dt):
            return dt.astimezone(dt_timezone.utc)
        return timezone.make_aware(dt, dt_timezone.utc)

    def fetch_new(
        self, *, source: Source, since: datetime | None = None, limit: int = 50
    ) -> list[RawItem]:
        if source.source_type != Source.SourceType.TELEGRAM:
            raise ValueError("TelegramAdapter can only be used with TELEGRAM sources.")
        if not source.identifier:
            raise ValueError("Telegram Source.identifier must be set (channel username/link/id).")

        # Pyrogram's sync layer expects an asyncio event loop in the current thread.
        # Under Gunicorn/thread executors, there may be no default loop.
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Import lazily so the rest of the backend can run without pyrogram installed.
        from pyrogram import Client  # type: ignore

        items: list[RawItem] = []
        since_utc = self._as_aware_utc(since)

        with Client(
            name="opportunity_finder_ingestion",
            api_id=self.api_id,
            api_hash=self.api_hash,
            session_string=self.session_string,
            in_memory=True,
        ) as app:
            # Newest-first iteration; we filter by 'since' manually.
            for msg in app.get_chat_history(source.identifier, limit=limit):
                if not msg:
                    continue
                if not getattr(msg, "id", None):
                    continue
                msg_date = self._as_aware_utc(getattr(msg, "date", None))
                if since_utc and msg_date and msg_date <= since_utc:
                    continue

                text = (getattr(msg, "text", None) or getattr(msg, "caption", None) or "").strip()
                if not text:
                    continue

                # Best-effort URL. For public channels, msg.link may exist.
                msg_url = getattr(msg, "link", None) or source.source_url or ""

                items.append(
                    RawItem(
                        external_id=str(msg.id),
                        source_url=msg_url,
                        published_at=msg_date,
                        raw_text=text,
                    )
                )

        return items


