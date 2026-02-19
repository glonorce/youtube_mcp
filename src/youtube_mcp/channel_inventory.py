"""youtube_mcp.channel_inventory

Intent:
    Fetch a single, bounded page of channel videos using the uploads playlist
    pipeline.

Depends on:
    - IYouTubeClient (DIP)
    - channel_resolver.resolve_channel
    - quota_budgeter
    - playlist_items_extract
    - video_classification
"""

from __future__ import annotations

from typing import Any, Sequence

from .channel_resolver import ResolvedChannel, resolve_channel
from .inventory_types import ChannelInventoryError, ChannelVideosPage, PartsLevel
from .playlist_items_extract import extract_video_ids
from .quota_budgeter import QuotaBudget, estimate_channel_videos_quota
from .video_classification import is_live, is_short
from .youtube_client_protocol import IYouTubeClient


def list_channel_videos_page(
    *,
    client: IYouTubeClient,
    channel_ref: str,
    max_videos: int,
    page_token: str | None,
    include_shorts: bool,
    include_live: bool,
    parts_level: PartsLevel,
    budget: QuotaBudget,
) -> ChannelVideosPage:
    quota_est = estimate_channel_videos_quota(
        strategy="uploads_playlist",
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
        raise ChannelInventoryError("uploadsPlaylistId not available for this channel")

    playlist_params: dict[str, str] = {"playlistId": uploads, "maxResults": "50"}
    if page_token:
        playlist_params["pageToken"] = page_token

    playlist_resp = client.playlist_items_list(part="snippet,contentDetails", params=playlist_params)

    truncated = False
    video_ids = extract_video_ids(playlist_resp.get("items"))
    if max_videos < len(video_ids):
        video_ids = video_ids[:max_videos]
        truncated = True

    if not video_ids:
        return ChannelVideosPage((), None, quota_est, False, 0)

    part = (
        "snippet,statistics,contentDetails"
        if parts_level == "basic"
        else "snippet,statistics,contentDetails,liveStreamingDetails,status"
    )
    videos_resp = client.videos_list(part=part, params={"id": ",".join(video_ids)})
    items = videos_resp.get("items")
    videos = items if isinstance(items, list) else []

    filtered = _filter_videos(videos, include_shorts=include_shorts, include_live=include_live)

    next_token = playlist_resp.get("nextPageToken")
    next_out = next_token if isinstance(next_token, str) and next_token else None

    return ChannelVideosPage(tuple(filtered), next_out, quota_est, truncated, len(video_ids))


def _filter_videos(videos: Sequence[dict[str, Any]], *, include_shorts: bool, include_live: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for v in videos:
        if not include_shorts and is_short(v):
            continue
        if not include_live and is_live(v):
            continue
        out.append(v)
    return out
