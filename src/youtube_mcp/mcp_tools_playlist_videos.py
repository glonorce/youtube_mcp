"""youtube_mcp.mcp_tools_playlist_videos

Intent:
    MCP tool handler(s) for playlist videos listing.
"""

from __future__ import annotations

import os
from typing import Any

from .playlist_videos import PartsLevel, list_playlist_videos_page
from .quota_budgeter import QuotaBudget
from .youtube_data_api_client import YouTubeDataApiClient, YouTubeDataApiClientConfig


def list_youtube_playlist_videos_tool(
    *,
    playlist_id: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
    max_items: int = 50,
    include_shorts: bool = False,
    include_live: bool = False,
    parts_level: PartsLevel = "basic",
) -> dict[str, Any]:
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not configured")

    if api_key.startswith("${") and api_key.endswith("}"):
        raise RuntimeError(
            "YOUTUBE_API_KEY appears to be an unexpanded placeholder (e.g. '${YOUTUBE_API_KEY}'). "
            "Your MCP host likely does not interpolate env vars inside mcp.json. "
            "Set YOUTUBE_API_KEY in the host process environment or paste the key directly in the MCP config."
        )

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key=api_key))
    budget = QuotaBudget(max_videos=200, max_pages=10, max_quota_units=1000)

    if page_token is None and next_page_token:
        page_token = next_page_token

    page = list_playlist_videos_page(
        client=client,
        playlist_id=playlist_id,
        page_token=page_token,
        max_items=max_items,
        include_shorts=include_shorts,
        include_live=include_live,
        parts_level=parts_level,
        budget=budget,
    )

    return {
        "items": list(page.items),
        "nextPageToken": page.next_page_token,
        "next_page_token": page.next_page_token,
        "quotaEstimate": {
            "estimatedUnits": page.quota_estimate.estimated_units,
            "strategy": page.quota_estimate.strategy,
            "notes": list(page.quota_estimate.notes),
        },
    }
