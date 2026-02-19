"""youtube_mcp.channel_videos_ordering_search

Intent:
    Search API strategy for channel videos.

Security/performance:
    - Expensive (quota ~100 per request) and capped.
    - Must be explicit opt-in at tool layer.
"""

from __future__ import annotations

from typing import Any

from .channel_resolver import ResolvedChannel, resolve_channel
from .inventory_types import ChannelVideosPage, PartsLevel
from .quota_budgeter import QuotaBudget, estimate_channel_videos_quota
from .video_sorting import filter_videos
from .youtube_client_protocol import IYouTubeClient


def list_channel_videos_search_api(
    *,
    client: IYouTubeClient,
    channel_ref: str,
    order_by: str,
    max_videos: int,
    page_token: str | None,
    include_shorts: bool,
    include_live: bool,
    parts_level: PartsLevel,
    budget: QuotaBudget,
) -> ChannelVideosPage:
    if order_by not in {"date", "viewCount"}:
        raise ValueError("search_api supports only order_by in {'date','viewCount'}")

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
        "order": order_by,
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
