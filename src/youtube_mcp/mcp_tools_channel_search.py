"""youtube_mcp.mcp_tools_channel_search

Intent:
    MCP tool handler for keyword-based video search within a channel.

Notes:
    - Uses YouTube Data API `search.list` (quota cost ~100 per page).
    - Supports pagination via `page_token` (and alias `next_page_token`).
"""

from __future__ import annotations

import os
from typing import Any

from .channel_search import SearchOrder, search_channel_videos_page
from .inventory_types import PartsLevel
from .quota_budgeter import QuotaBudget
from .youtube_data_api_client import YouTubeDataApiClient, YouTubeDataApiClientConfig


def search_youtube_channel_videos_tool(
    *,
    channel_ref: str,
    query: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
    max_videos: int = 50,
    include_shorts: bool = False,
    include_live: bool = False,
    parts_level: PartsLevel = "basic",
    order: SearchOrder = "relevance",
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

    if page_token is None and next_page_token:
        page_token = next_page_token

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key=api_key))
    budget = QuotaBudget(max_videos=200, max_pages=10, max_quota_units=1000)

    page = search_channel_videos_page(
        client=client,
        channel_ref=channel_ref,
        query=query,
        page_token=page_token,
        max_videos=max_videos,
        include_shorts=include_shorts,
        include_live=include_live,
        parts_level=parts_level,
        order=order,
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
        "appliedOrder": {"order": order},
    }
