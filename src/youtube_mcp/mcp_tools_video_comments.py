"""youtube_mcp.mcp_tools_video_comments

Intent:
    MCP tool handler for listing YouTube video comment threads.

Notes:
    - Uses commentThreads.list (public comments)
    - Supports pagination via `page_token` (and alias `next_page_token`)
"""

from __future__ import annotations

import os
from typing import Any

from .quota_budgeter import QuotaBudget
from .video_comments import (
    CommentOrder,
    TextFormat,
    list_video_comment_threads_page,
)
from .youtube_data_api_client import YouTubeDataApiClient, YouTubeDataApiClientConfig


def list_youtube_video_comments_tool(
    *,
    video_id: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
    max_threads: int = 100,
    order: CommentOrder = "relevance",
    text_format: TextFormat = "plainText",
    include_replies: bool = False,
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

    page = list_video_comment_threads_page(
        client=client,
        video_id=video_id,
        page_token=page_token,
        max_threads=max_threads,
        order=order,
        text_format=text_format,
        include_replies=include_replies,
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
