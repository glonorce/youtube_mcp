"""Unit tests for channel_search."""

from __future__ import annotations

import pytest

from src.youtube_mcp.channel_search import search_channel_videos_page
from src.youtube_mcp.quota_budgeter import QuotaBudget


class _FakeClient:
    def channels_list(self, *, part: str, params):
        return {
            "items": [
                {
                    "id": "UC_x",
                    "snippet": {"title": "T", "customUrl": "@Handle"},
                    "contentDetails": {"relatedPlaylists": {"uploads": "UU_x"}},
                }
            ]
        }

    def search_list(self, *, part: str, params):
        assert params["q"] == "hello"
        return {"items": [{"id": {"videoId": "v1"}}, {"id": {"videoId": "v2"}}], "nextPageToken": "NEXT"}

    def videos_list(self, *, part: str, params):
        ids = params["id"].split(",")
        return {
            "items": [
                {
                    "id": vid,
                    "snippet": {"liveBroadcastContent": "none"},
                    "contentDetails": {"duration": "PT5M"},
                    "statistics": {"viewCount": "1"},
                }
                for vid in ids
            ]
        }

    def playlists_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def playlist_items_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def comment_threads_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_search_channel_videos_returns_next_token() -> None:
    client = _FakeClient()
    page = search_channel_videos_page(
        client=client,
        channel_ref="@Handle",
        query="hello",
        page_token=None,
        max_videos=50,
        include_shorts=True,
        include_live=True,
        parts_level="basic",
        order="relevance",
        budget=QuotaBudget(max_videos=200, max_pages=10, max_quota_units=1000),
    )

    assert page.next_page_token == "NEXT"
    assert len(page.items) == 2
