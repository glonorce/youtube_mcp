"""youtube_mcp.playlist_items_extract

Intent:
    Extract video IDs from `playlistItems.list` responses.

Why:
    - Keep extraction logic deterministic and validated.
    - Reduce duplication across channel inventory and playlist listing.

This module does not perform network calls.
"""

from __future__ import annotations

from typing import Any, Iterable


def extract_video_ids(items: Any, *, limit: int | None = None) -> list[str]:
    """Extract `snippet.resourceId.videoId` values.

    Args:
        items: value of response['items']
        limit: optional max number of IDs to return

    Returns:
        List of video IDs (deduplicated, stable order).
    """

    if not isinstance(items, list):
        return []

    out: list[str] = []
    seen: set[str] = set()

    for it in items:
        if limit is not None and len(out) >= limit:
            break

        if not isinstance(it, dict):
            continue
        snippet = it.get("snippet")
        if not isinstance(snippet, dict):
            continue
        resource = snippet.get("resourceId")
        if not isinstance(resource, dict):
            continue
        vid = resource.get("videoId")
        if not isinstance(vid, str) or not vid:
            continue

        if vid in seen:
            continue

        seen.add(vid)
        out.append(vid)

    return out
