from __future__ import annotations

import re
from datetime import date


_DEADLINE_RE_ISO = re.compile(r"\bdeadline\b[^0-9]{0,20}(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
_DEADLINE_RE_MDY = re.compile(
    r"\bdeadline\b[^A-Za-z]{0,20}([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?[, ]+\s*(\d{4})",
    re.IGNORECASE,
)

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def extract_deadline_fast(text: str) -> date | None:
    """
    Cheap deadline extractor for common patterns.
    Avoids an AI call and helps with deduped rows / older extracted rows.
    """
    t = text or ""
    m = _DEADLINE_RE_ISO.search(t)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except Exception:
            return None

    m = _DEADLINE_RE_MDY.search(t)
    if not m:
        return None

    month = _MONTHS.get((m.group(1) or "").strip().lower())
    if not month:
        return None
    try:
        day = int(m.group(2))
        year = int(m.group(3))
        return date(year, month, day)
    except Exception:
        return None


