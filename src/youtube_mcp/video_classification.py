"""youtube_mcp.video_classification

Intent:
    Best-effort classification helpers for YouTube videos.

Why:
    - Keep heuristics in one place (SSOT).
    - Avoid duplication across channel inventory and playlist listing.

Important:
    These heuristics are not authoritative. Callers must treat them as
    *best-effort* and expose this fact to clients.
"""

from __future__ import annotations

import re
from typing import Any, Mapping


_DURATION_RE = re.compile(r"^PT(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?$")


def parse_duration_seconds(duration: str) -> int | None:
    """Parse ISO-8601 duration as seconds.

    Supports the subset commonly returned by YouTube, e.g.:
        PT30S, PT5M, PT1H2M3S

    Returns None if parsing fails.
    """

    m = _DURATION_RE.match(duration)
    if not m:
        return None

    h = int(m.group("h") or 0)
    mi = int(m.group("m") or 0)
    s = int(m.group("s") or 0)

    # Guard: avoid ridiculous numbers.
    if h < 0 or mi < 0 or s < 0:
        return None

    return h * 3600 + mi * 60 + s


def is_short(video: Mapping[str, Any]) -> bool:
    """Best-effort: duration <= 60s."""

    cd = video.get("contentDetails")
    if not isinstance(cd, dict):
        return False

    duration = cd.get("duration")
    if not isinstance(duration, str):
        return False

    seconds = parse_duration_seconds(duration)
    return seconds is not None and seconds <= 60


def is_live(video: Mapping[str, Any]) -> bool:
    """Best-effort: snippet.liveBroadcastContent in {live, upcoming}."""

    snippet = video.get("snippet")
    if not isinstance(snippet, dict):
        return False

    live = snippet.get("liveBroadcastContent")
    return isinstance(live, str) and live in {"live", "upcoming"}
