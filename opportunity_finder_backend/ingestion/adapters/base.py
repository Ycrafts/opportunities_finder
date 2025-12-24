from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from opportunities.models import Source


@dataclass(frozen=True)
class RawItem:
    """
    Normalized raw message/item emitted by an adapter.
    This maps 1:1 into opportunities.RawOpportunity fields later.
    """

    external_id: str
    source_url: str
    published_at: datetime | None
    raw_text: str


class BaseAdapter(ABC):
    """
    Source adapter interface.

    Adapters fetch new items from a Source and return RawItem records.
    They do NOT write to the database directly (writer/runner layer handles that).
    """

    @abstractmethod
    def fetch_new(
        self, *, source: Source, since: datetime | None = None, limit: int = 50
    ) -> list[RawItem]:
        raise NotImplementedError


