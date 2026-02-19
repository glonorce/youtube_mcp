"""youtube_mcp.playlist_videos

Intent:
    List one page of videos in a playlist with optional enrichment.

Depends on SSOT helpers:
    - playlist_items_extract.extract_video_ids
    - video_classification (short/live)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Sequence

from .playlist_items_extract import extract_video_ids
from .quota_budgeter import QuotaBudget, QuotaEstimate, QUOTA_COST_READ
from .video_classification import is_live, is_short
from .youtube_client_protocol import IYouTubeClient


PartsLevel = Literal["basic", "full"]


@dataclass(frozen=True, slots=True)
class PlaylistVideosPage:
    items: tuple[dict[str, Any], ...]
    next_page_token: str | None
    quota_estimate: QuotaEstimate


def list_playlist_videos_page(
    *,
    client: IYouTubeClient,
    playlist_id: str,
    page_token: str | None,
    max_items: int,
    include_shorts: bool,
    include_live: bool,
    parts_level: PartsLevel,
    budget: QuotaBudget,
) -> PlaylistVideosPage:
    if not playlist_id or not playlist_id.strip():
        raise ValueError("playlist_id is required")
    if max_items <= 0:
        raise ValueError("max_items must be positive")

    units = QUOTA_COST_READ + QUOTA_COST_READ
    if units > budget.max_quota_units:
        raise ValueError("Quota budget too low")

    params: dict[str, str] = {"playlistId": playlist_id, "maxResults": "50"}
    if page_token:
        params["pageToken"] = page_token

    resp = client.playlist_items_list(part="snippet,contentDetails", params=params)
    ids = extract_video_ids(resp.get("items"), limit=max_items)
    if not ids:
        return PlaylistVideosPage((), None, QuotaEstimate(estimated_units=QUOTA_COST_READ, strategy="uploads_playlist", notes=()))

    part = "snippet,statistics,contentDetails" if parts_level == "basic" else "snippet,statistics,contentDetails,liveStreamingDetails,status"
    videos_resp = client.videos_list(part=part, params={"id": ",".join(ids)})
    items = videos_resp.get("items")
    videos = items if isinstance(items, list) else []

    filtered = _filter_videos(videos, include_shorts=include_shorts, include_live=include_live)

    next_token = resp.get("nextPageToken")
    next_out = next_token if isinstance(next_token, str) and next_token else None

    return PlaylistVideosPage(tuple(filtered), next_out, QuotaEstimate(estimated_units=units, strategy="uploads_playlist", notes=()))


def _filter_videos(videos: Sequence[dict[str, Any]], *, include_shorts: bool, include_live: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for v in videos:
        if not include_shorts and is_short(v):
            continue
        if not include_live and is_live(v):
            continue
        out.append(v)
    return out
