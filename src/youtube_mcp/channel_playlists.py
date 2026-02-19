"""youtube_mcp.channel_playlists

Intent:
    List public playlists for a channel using YouTube Data API v3.

Properties:
    - Paginated (pageToken)
    - Budgeted (max_pages/quota) - conservative estimate

Non-goals:
    - Listing private playlists (not possible without OAuth / permissions).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .channel_resolver import ResolvedChannel, resolve_channel
from .quota_budgeter import QuotaBudget, QuotaEstimate, QUOTA_COST_READ
from .youtube_client_protocol import IYouTubeClient


@dataclass(frozen=True, slots=True)
class ChannelPlaylistsPage:
    items: tuple[dict[str, Any], ...]
    next_page_token: str | None
    quota_estimate: QuotaEstimate


def list_channel_playlists_page(
    *,
    client: IYouTubeClient,
    channel_ref: str,
    page_token: str | None,
    budget: QuotaBudget,
) -> ChannelPlaylistsPage:
    """List one page of a channel's public playlists."""

    # Resolve channelId (strict)
    resolved: ResolvedChannel = resolve_channel(
        client=client,
        channel_ref=channel_ref,
        mode="strict",
        include_uploads_playlist=False,
    )

    params: dict[str, str] = {
        "channelId": resolved.channel_id,
        "maxResults": "50",
    }
    if page_token:
        params["pageToken"] = page_token

    # Conservative estimate: 1 unit per page
    est = QuotaEstimate(estimated_units=QUOTA_COST_READ, strategy="uploads_playlist", notes=())

    resp = client.playlists_list(part="snippet,contentDetails", params=params)
    items = resp.get("items")
    if not isinstance(items, list):
        items = []

    next_token = resp.get("nextPageToken")
    next_out = next_token if isinstance(next_token, str) and next_token else None

    return ChannelPlaylistsPage(items=tuple(items), next_page_token=next_out, quota_estimate=est)
