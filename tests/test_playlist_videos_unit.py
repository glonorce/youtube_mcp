"""Unit tests for playlist_videos."""

from __future__ import annotations

from src.youtube_mcp.playlist_videos import list_playlist_videos_page
from src.youtube_mcp.quota_budgeter import QuotaBudget


class _FakeClient:
    def playlist_items_list(self, *, part: str, params):
        return {
            "items": [
                {"snippet": {"resourceId": {"videoId": "v1"}}},
                {"snippet": {"resourceId": {"videoId": "v2"}}},
            ],
            "nextPageToken": "N",
        }

    def videos_list(self, *, part: str, params):
        ids = params["id"].split(",")
        items = []
        for vid in ids:
            items.append(
                {
                    "id": vid,
                    "snippet": {"liveBroadcastContent": "none"},
                    "contentDetails": {"duration": "PT30S" if vid == "v2" else "PT5M"},
                    "statistics": {"viewCount": "1"},
                }
            )
        return {"items": items}

    # unused
    def channels_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def playlists_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def search_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_playlist_videos_excludes_shorts_by_default() -> None:
    client = _FakeClient()
    page = list_playlist_videos_page(
        client=client,
        playlist_id="PL_x",
        page_token=None,
        max_items=50,
        include_shorts=False,
        include_live=True,
        parts_level="basic",
        budget=QuotaBudget(max_quota_units=1000),
    )
    ids = {it["id"] for it in page.items}
    assert "v2" not in ids
    assert page.next_page_token == "N"
