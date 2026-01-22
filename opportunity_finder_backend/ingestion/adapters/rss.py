from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Optional
from urllib import request
from xml.etree import ElementTree

from django.utils.html import strip_tags

from opportunities.models import Source

from .base import BaseAdapter, RawItem


class RssAdapter(BaseAdapter):
    """
    RSS ingestion via XML parsing.

    Expects:
      - source.source_type == RSS
      - source.identifier contains feed URL
    """

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

    def _find_text(self, item: ElementTree.Element, tag: str) -> str:
        node = item.find(tag)
        if node is not None and node.text:
            return node.text.strip()
        return ""

    def _find_text_ns(self, item: ElementTree.Element, tag: str, ns: dict[str, str]) -> str:
        node = item.find(tag, ns)
        if node is not None and node.text:
            return node.text.strip()
        return ""

    def fetch_new(
        self, *, source: Source, since: datetime | None = None, limit: int = 50
    ) -> list[RawItem]:
        if source.source_type != Source.SourceType.RSS:
            raise ValueError("RssAdapter can only be used with RSS sources.")
        if not source.identifier:
            raise ValueError("RSS Source.identifier must be set to a feed URL.")

        req = request.Request(
            source.identifier,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with request.urlopen(req, timeout=20) as response:
            payload = response.read()

        root = ElementTree.fromstring(payload)
        ns = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        items: list[RawItem] = []
        for entry in root.findall("./channel/item"):
            title = self._find_text(entry, "title")
            link = self._find_text(entry, "link")
            guid = self._find_text(entry, "guid")
            description = self._find_text(entry, "description")
            content = self._find_text_ns(entry, "content:encoded", ns)
            pub_date = self._find_text(entry, "pubDate")
            published_at = self._parse_date(pub_date)

            raw_html = content or description or ""
            raw_text = strip_tags(unescape(raw_html)).strip()
            if title and raw_text:
                combined = f"{title}\n\n{raw_text}"
            else:
                combined = title or raw_text

            if not combined:
                continue

            items.append(
                RawItem(
                    external_id=guid or link,
                    source_url=link or source.identifier,
                    published_at=published_at,
                    raw_text=combined,
                )
            )

            if len(items) >= limit:
                break

        return items
