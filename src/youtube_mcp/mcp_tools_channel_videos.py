"""youtube_mcp.mcp_tools_channel_videos

Intent:
    MCP tool handler(s) for channel video inventory listing.

Notes:
    - Safe-by-default: shorts/live excluded unless explicitly enabled.
    - Budgeted: quota and max-videos limits enforced.
    - Ordering is explicit opt-in; expensive strategies are guarded.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from .channel_videos_ordering import OrderBy, OrderStrategy, list_channel_videos
from .inventory_types import PartsLevel
from .quota_budgeter import QuotaBudget
from .youtube_data_api_client import YouTubeDataApiClient, YouTubeDataApiClientConfig


def list_youtube_channel_videos_tool(
    *,
    channel_ref: str,
    max_videos: int = 200,
    page_token: str | None = None,
    next_page_token: str | None = None,
    include_shorts: bool = False,
    include_live: bool = False,
    parts_level: PartsLevel = "basic",
    order_strategy: OrderStrategy = "uploads_playlist",
    order_by: OrderBy = "date",
) -> dict[str, Any]:
    """Tool handler: list channel videos.

    Args:
        order_strategy:
            - uploads_playlist (default)
            - local_sort (bounded subset, returns sorted items, not paginated)
            - search_api (expensive, capped)
        order_by:
            - date, viewCount, likeCount, commentCount, duration
    """

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

    # Pagination alias:
    # Some agents look for `next_page_token` instead of `page_token`.
    # If provided, treat it as `page_token`.
    if page_token is None and next_page_token:
        page_token = next_page_token

    page = list_channel_videos(
        client=client,
        channel_ref=channel_ref,
        strategy=order_strategy,
        order_by=order_by,
        max_videos=max_videos,
        page_token=page_token,
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
        "truncated": page.truncated,
        "appliedMaxVideos": page.applied_max_videos,
        "appliedOrder": {"strategy": order_strategy, "by": order_by},
    }
