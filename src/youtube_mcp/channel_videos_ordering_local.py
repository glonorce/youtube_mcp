"""youtube_mcp.channel_videos_ordering_local

Intent:
    Local-sort strategy for channel videos.

Properties:
    - Bounded: uses max_videos and budget.max_pages.
    - Not paginated: page_token must be None.
"""

from __future__ import annotations

from typing import Any

from .channel_resolver import ResolvedChannel, resolve_channel
from .inventory_types import ChannelVideosPage, PartsLevel
from .playlist_items_extract import extract_video_ids
from .quota_budgeter import QuotaBudget, estimate_channel_videos_quota
from .video_sorting import filter_videos, sort_key
from .youtube_client_protocol import IYouTubeClient


def list_channel_videos_local_sorted(
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
    if page_token:
        raise ValueError("page_token is not supported for local_sort")

    quota_est = estimate_channel_videos_quota(
        strategy="local_sort",
        requested_max_videos=max_videos,
        budget=budget,
        include_video_details=True,
    )

    resolved: ResolvedChannel = resolve_channel(
        client=client,
        channel_ref=channel_ref,
        mode="strict",
        include_uploads_playlist=True,
    )

    uploads = resolved.uploads_playlist_id
    if not uploads:
        raise ValueError("uploadsPlaylistId not available")

    ids: list[str] = []
    token: str | None = None
    pages = 0

    while len(ids) < max_videos and pages < budget.max_pages:
        params = {"playlistId": uploads, "maxResults": "50"}
        if token:
            params["pageToken"] = token

        resp = client.playlist_items_list(part="snippet,contentDetails", params=params)
        ids.extend(extract_video_ids(resp.get("items")))
        pages += 1

        token_val = resp.get("nextPageToken")
        token = token_val if isinstance(token_val, str) and token_val else None
        if not token:
            break

    truncated = len(ids) > max_videos or (token is not None)
    ids = ids[:max_videos]

    part = (
        "snippet,statistics,contentDetails"
        if parts_level == "basic"
        else "snippet,statistics,contentDetails,liveStreamingDetails,status"
    )

    videos: list[dict[str, Any]] = []
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        vresp = client.videos_list(part=part, params={"id": ",".join(batch)})
        items = vresp.get("items")
        if isinstance(items, list):
            videos.extend([v for v in items if isinstance(v, dict)])

    filtered = filter_videos(videos, include_shorts=include_shorts, include_live=include_live)
    sorted_items = sorted(filtered, key=lambda v: sort_key(v, order_by), reverse=True)

    return ChannelVideosPage(tuple(sorted_items), None, quota_est, truncated, len(ids))
