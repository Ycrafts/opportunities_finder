from __future__ import annotations

import hashlib
from dataclasses import dataclass

from django.db import transaction

from opportunities.models import RawOpportunity, Source

from ingestion.adapters.base import RawItem


@dataclass(frozen=True)
class WriteResult:
    created: int
    updated: int


class RawOpportunityWriter:
    """
    Idempotent writer: upserts RawOpportunity rows.

    Key rule:
      - unique key is (source, external_id)
    """

    def _normalize_external_id(self, source: Source, item: RawItem) -> str:
        """
        Ensure external_id is stable and non-empty.

        Telegram will provide message ids, but RSS/web might not.
        When missing, we derive one from URL or content.
        """
        if item.external_id and item.external_id.strip():
            return item.external_id.strip()

        # Prefer URL-based identity when available.
        if item.source_url and item.source_url.strip():
            base = f"url:{item.source_url.strip()}"
        else:
            # Fallback: stable content hash (best-effort).
            base = f"text:{item.raw_text.strip()}"

        digest = hashlib.sha1(base.encode("utf-8")).hexdigest()  # stable, short enough
        return digest

    @transaction.atomic
    def upsert_items(self, *, source: Source, items: list[RawItem]) -> WriteResult:
        created = 0
        updated = 0

        for item in items:
            ext_id = self._normalize_external_id(source, item)

            obj, was_created = RawOpportunity.objects.update_or_create(
                source=source,
                external_id=ext_id,
                defaults={
                    "source_url": item.source_url or "",
                    "raw_text": item.raw_text or "",
                    "published_at": item.published_at,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

            # Ensure NEW is kept for newly ingested items; do not overwrite status here.
            # (translation/extraction pipeline will update status later)
            if was_created and obj.status != RawOpportunity.ProcessingStatus.NEW:
                obj.status = RawOpportunity.ProcessingStatus.NEW
                obj.save(update_fields=["status"])

        return WriteResult(created=created, updated=updated)


