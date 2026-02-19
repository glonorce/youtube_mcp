"""youtube_mcp.mcp_tools_channel_playlists

Intent:
    MCP tool handler(s) for channel playlists listing.
"""

from __future__ import annotations

import os
from typing import Any

from .channel_playlists import list_channel_playlists_page
from .quota_budgeter import QuotaBudget
from .youtube_data_api_client import YouTubeDataApiClient, YouTubeDataApiClientConfig


def list_youtube_channel_playlists_tool(
    *,
    channel_ref: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
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

    page = list_channel_playlists_page(client=client, channel_ref=channel_ref, page_token=page_token, budget=budget)

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
