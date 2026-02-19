"""Unit tests for channel_videos_ordering."""

from __future__ import annotations

import pytest

from src.youtube_mcp.channel_videos_ordering import list_channel_videos
from src.youtube_mcp.quota_budgeter import QuotaBudget


class _FakeClient:
    def channels_list(self, *, part: str, params):
        # uploads playlist present
        return {
            "items": [
                {
                    "id": "UC_x",
                    "snippet": {"title": "T"},
                    "contentDetails": {"relatedPlaylists": {"uploads": "UU_x"}},
                }
            ]
        }

    def playlist_items_list(self, *, part: str, params):
        return {
            "items": [
                {"snippet": {"resourceId": {"videoId": "v1"}}},
                {"snippet": {"resourceId": {"videoId": "v2"}}},
            ]
        }

    def videos_list(self, *, part: str, params):
        ids = params["id"].split(",")
        items = []
        for vid in ids:
            items.append(
                {
                    "id": vid,
                    "snippet": {"liveBroadcastContent": "none"},
                    "contentDetails": {"duration": "PT5M"},
                    "statistics": {"viewCount": "2" if vid == "v2" else "1"},
                }
            )
        return {"items": items}

    def search_list(self, *, part: str, params):
        return {
            "items": [
                {"id": {"videoId": "v1"}},
                {"id": {"videoId": "v2"}},
            ]
        }

    def playlists_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_local_sort_orders_by_viewcount() -> None:
    client = _FakeClient()
    page = list_channel_videos(
        client=client,
        channel_ref="@Handle",
        strategy="local_sort",
        order_by="viewCount",
        max_videos=2,
        page_token=None,
        include_shorts=True,
        include_live=True,
        parts_level="basic",
        budget=QuotaBudget(max_pages=1, max_quota_units=1000),
    )
    assert page.items[0]["id"] == "v2"


def test_search_api_rejects_unsupported_order_by() -> None:
    client = _FakeClient()
    with pytest.raises(ValueError):
        list_channel_videos(
            client=client,
            channel_ref="@Handle",
            strategy="search_api",
            order_by="likeCount",
            max_videos=10,
            page_token=None,
            include_shorts=True,
            include_live=True,
            parts_level="basic",
            budget=QuotaBudget(max_quota_units=10_000),
        )
