"""Unit tests for channel_inventory.

Intent:
    Verify bounded, paginated inventory pipeline using a fake YouTube client.
"""

from __future__ import annotations

import pytest

from src.youtube_mcp.channel_inventory import list_channel_videos_page
from src.youtube_mcp.quota_budgeter import QuotaBudget


class _FakeClient:
    def __init__(self):
        self._calls = []

    def channels_list(self, *, part: str, params):
        # Return uploads playlist id
        return {
            "items": [
                {
                    "id": "UC_x",
                    "snippet": {"title": "T", "customUrl": "@Handle"},
                    "contentDetails": {"relatedPlaylists": {"uploads": "UU_x"}},
                }
            ]
        }

    def playlist_items_list(self, *, part: str, params):
        self._calls.append(("playlist_items_list", params))
        return {
            "items": [
                {"snippet": {"resourceId": {"videoId": "v1"}}},
                {"snippet": {"resourceId": {"videoId": "v2"}}},
                {"snippet": {"resourceId": {"videoId": "v3"}}},
            ],
            "nextPageToken": "NEXT",
        }

    def videos_list(self, *, part: str, params):
        self._calls.append(("videos_list", params))
        ids = params.get("id", "").split(",")
        # Mark v3 as short (PT30S)
        items = []
        for vid in ids:
            item = {
                "id": vid,
                "snippet": {"liveBroadcastContent": "none"},
                "contentDetails": {"duration": "PT30S" if vid == "v3" else "PT5M"},
                "statistics": {"viewCount": "1"},
            }
            items.append(item)
        return {"items": items}

    def playlists_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def search_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_inventory_page_truncates_to_max_videos() -> None:
    client = _FakeClient()
    page = list_channel_videos_page(
        client=client,
        channel_ref="@Handle",
        max_videos=2,
        page_token=None,
        include_shorts=True,
        include_live=True,
        parts_level="basic",
        budget=QuotaBudget(max_videos=200, max_pages=10, max_quota_units=1000),
    )
    assert page.applied_max_videos == 2
    assert page.truncated is True
    assert page.next_page_token == "NEXT"
    assert len(page.items) == 2


def test_inventory_excludes_shorts_by_default() -> None:
    client = _FakeClient()
    page = list_channel_videos_page(
        client=client,
        channel_ref="@Handle",
        max_videos=10,
        page_token=None,
        include_shorts=False,
        include_live=True,
        parts_level="basic",
        budget=QuotaBudget(max_videos=200, max_pages=10, max_quota_units=1000),
    )
    ids = {it["id"] for it in page.items}
    assert "v3" not in ids
