from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TokenStore:
    def __init__(self, path: str = "data/tokens.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def get_refresh_token(self, user_id: int) -> str | None:
        data = self._read()
        return data.get(str(user_id))

    def set_refresh_token(self, user_id: int, refresh_token: str) -> None:
        data = self._read()
        data[str(user_id)] = refresh_token
        self._write(data)

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
