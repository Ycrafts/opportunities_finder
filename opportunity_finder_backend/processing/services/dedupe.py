from __future__ import annotations

import hashlib
import re


_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_HANDLE_RE = re.compile(r"@\w+", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def normalize_for_hash(text: str) -> str:
    """
    Best-effort normalization for near-duplicate detection.

    Goal: reduce noise from links/handles/formatting, while preserving the core content.
    """
    t = (text or "").strip().lower()
    if not t:
        return ""

    # Remove URLs + handles (these frequently change between reposts).
    t = _URL_RE.sub(" ", t)
    t = _HANDLE_RE.sub(" ", t)

    # Remove common "status" markers so a later CLOSED repost still hashes like the original.
    for marker in [
        "‼️closed‼️",
        "closed",
        "#closed",
        "vacancy filled",
        "position filled",
        "applications closed",
        "application closed",
        "hiring closed",
        "no longer accepting applications",
    ]:
        t = t.replace(marker, " ")

    # Strip most punctuation but keep letters/numbers/spaces.
    t = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in t)

    # Collapse whitespace.
    t = _WS_RE.sub(" ", t).strip()
    return t


def compute_content_hash(text: str) -> str:
    norm = normalize_for_hash(text)
    if not norm:
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


