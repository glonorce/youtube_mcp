"""youtube_mcp.channel_search

Intent:
    Search for videos within a specific channel using YouTube Data API `search.list`.

Why:
    - Enables keyword-based discovery without enumerating the entire uploads playlist.

Important limitations (YouTube API behavior):
    - `search.list` is **expensive** (quota cost ~100 units per request).
    - When using `channelId` + `type=video`, results are constrained (commonly noted as <= 500).

Pagination:
    - Supported via `pageToken` -> `nextPageToken`.

Non-goals:
    - This is public-data only and uses API key (no OAuth).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .channel_resolver import ResolvedChannel, resolve_channel
from .inventory_types import ChannelVideosPage, PartsLevel
from .quota_budgeter import QuotaBudget, estimate_channel_videos_quota
from .video_sorting import filter_videos
from .youtube_client_protocol import IYouTubeClient


SearchOrder = Literal["date", "viewCount", "relevance", "rating", "title"]


@dataclass(frozen=True, slots=True)
class ChannelSearchPage:
    items: tuple[dict[str, Any], ...]
    next_page_token: str | None
    quota_estimate: Any


def search_channel_videos_page(
    *,
    client: IYouTubeClient,
    channel_ref: str,
    query: str,
    page_token: str | None,
    max_videos: int,
    include_shorts: bool,
    include_live: bool,
    parts_level: PartsLevel,
    order: SearchOrder,
    budget: QuotaBudget,
) -> ChannelVideosPage:
    if not query or not query.strip():
        raise ValueError("query is required")

    quota_est = estimate_channel_videos_quota(
        strategy="search_api",
        requested_max_videos=max_videos,
        budget=budget,
        include_video_details=True,
    )

    resolved: ResolvedChannel = resolve_channel(
        client=client,
        channel_ref=channel_ref,
        mode="strict",
        include_uploads_playlist=False,
    )

    params: dict[str, str] = {
        "channelId": resolved.channel_id,
        "type": "video",
        "q": query,
        "order": order,
        "maxResults": "50",
    }
    if page_token:
        params["pageToken"] = page_token

    resp = client.search_list(part="snippet", params=params)
    ids = _extract_search_video_ids(resp.get("items"), limit=max_videos)
    if not ids:
        return ChannelVideosPage((), None, quota_est, False, 0)

    part = (
        "snippet,statistics,contentDetails"
        if parts_level == "basic"
        else "snippet,statistics,contentDetails,liveStreamingDetails,status"
    )

    videos_resp = client.videos_list(part=part, params={"id": ",".join(ids)})
    items = videos_resp.get("items")
    videos = items if isinstance(items, list) else []

    filtered = filter_videos(videos, include_shorts=include_shorts, include_live=include_live)

    next_token = resp.get("nextPageToken")
    next_out = next_token if isinstance(next_token, str) and next_token else None

    return ChannelVideosPage(tuple(filtered), next_out, quota_est, False, len(ids))


def _extract_search_video_ids(items: Any, *, limit: int) -> list[str]:
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for it in items:
        if len(out) >= limit:
            break
        if not isinstance(it, dict):
            continue
        id_block = it.get("id")
        if not isinstance(id_block, dict):
            continue
        vid = id_block.get("videoId")
        if isinstance(vid, str) and vid:
            out.append(vid)
    return out
