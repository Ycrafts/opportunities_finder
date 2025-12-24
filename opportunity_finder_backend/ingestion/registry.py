from __future__ import annotations

from typing import Type

from opportunities.models import Source

from ingestion.adapters.base import BaseAdapter
from ingestion.adapters.telegram import TelegramAdapter


class AdapterRegistry:
    """
    Maps SourceType -> Adapter class.
    Keeps runner logic clean and extensible.
    """

    def __init__(self):
        self._map: dict[str, Type[BaseAdapter]] = {
            Source.SourceType.TELEGRAM: TelegramAdapter,
        }

    def get_adapter_class(self, source_type: str) -> Type[BaseAdapter]:
        if source_type not in self._map:
            raise KeyError(f"No adapter registered for source_type={source_type}")
        return self._map[source_type]


