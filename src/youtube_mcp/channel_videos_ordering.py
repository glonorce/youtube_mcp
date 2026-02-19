"""youtube_mcp.channel_videos_ordering

Intent:
    Facade/dispatcher for channel video ordering strategies.

This module must stay small; strategy implementations live in:
    - channel_videos_ordering_local
    - channel_videos_ordering_search
"""

from __future__ import annotations

from typing import Literal

from .channel_inventory import list_channel_videos_page
from .channel_videos_ordering_local import list_channel_videos_local_sorted
from .channel_videos_ordering_search import list_channel_videos_search_api
from .inventory_types import ChannelVideosPage, PartsLevel
from .quota_budgeter import QuotaBudget
from .youtube_client_protocol import IYouTubeClient


OrderStrategy = Literal["uploads_playlist", "local_sort", "search_api"]
OrderBy = Literal["date", "viewCount", "likeCount", "commentCount", "duration"]


def list_channel_videos(
    *,
    client: IYouTubeClient,
    channel_ref: str,
    strategy: OrderStrategy,
    order_by: OrderBy,
    max_videos: int,
    page_token: str | None,
    include_shorts: bool,
    include_live: bool,
    parts_level: PartsLevel,
    budget: QuotaBudget,
) -> ChannelVideosPage:
    if strategy == "uploads_playlist":
        return list_channel_videos_page(
            client=client,
            channel_ref=channel_ref,
            max_videos=max_videos,
            page_token=page_token,
            include_shorts=include_shorts,
            include_live=include_live,
            parts_level=parts_level,
            budget=budget,
        )

    if strategy == "local_sort":
        return list_channel_videos_local_sorted(
            client=client,
            channel_ref=channel_ref,
            order_by=order_by,
            max_videos=max_videos,
            page_token=page_token,
            include_shorts=include_shorts,
            include_live=include_live,
            parts_level=parts_level,
            budget=budget,
        )

    if strategy == "search_api":
        return list_channel_videos_search_api(
            client=client,
            channel_ref=channel_ref,
            order_by=order_by,
            max_videos=max_videos,
            page_token=page_token,
            include_shorts=include_shorts,
            include_live=include_live,
            parts_level=parts_level,
            budget=budget,
        )

    raise ValueError(f"Unknown strategy: {strategy}")
