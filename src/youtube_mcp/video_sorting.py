"""youtube_mcp.video_sorting

Intent:
    Domain-specific helpers for filtering and sorting YouTube video dicts.

Why:
    - SSOT for filtering shorts/live.
    - SSOT for sorting keys used by local_sort.

This is not a generic utils module.
"""

from __future__ import annotations

from typing import Any, Sequence

from .video_classification import is_live, is_short, parse_duration_seconds


def filter_videos(
    videos: Sequence[dict[str, Any]],
    *,
    include_shorts: bool,
    include_live: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for v in videos:
        if not include_shorts and is_short(v):
            continue
        if not include_live and is_live(v):
            continue
        out.append(v)
    return out


def sort_key(video: dict[str, Any], order_by: str) -> int:
    stats = video.get("statistics") if isinstance(video.get("statistics"), dict) else {}

    if order_by == "viewCount":
        return int(stats.get("viewCount", 0) or 0)
    if order_by == "likeCount":
        return int(stats.get("likeCount", 0) or 0)
    if order_by == "commentCount":
        return int(stats.get("commentCount", 0) or 0)
    if order_by == "duration":
        cd = video.get("contentDetails") if isinstance(video.get("contentDetails"), dict) else {}
        dur = cd.get("duration")
        return (parse_duration_seconds(dur) or 0) if isinstance(dur, str) else 0

    return 0
