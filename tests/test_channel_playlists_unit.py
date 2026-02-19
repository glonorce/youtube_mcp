"""Unit tests for channel_playlists."""

from __future__ import annotations

from src.youtube_mcp.channel_playlists import list_channel_playlists_page
from src.youtube_mcp.quota_budgeter import QuotaBudget


class _FakeClient:
    def channels_list(self, *, part: str, params):
        return {"items": [{"id": "UC_x", "snippet": {"title": "T"}}]}

    def playlists_list(self, *, part: str, params):
        assert params["channelId"] == "UC_x"
        return {"items": [{"id": "PL_1"}], "nextPageToken": "N"}

    # unused
    def playlist_items_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def videos_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def search_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_list_channel_playlists_page() -> None:
    client = _FakeClient()
    page = list_channel_playlists_page(
        client=client,
        channel_ref="@Handle",
        page_token=None,
        budget=QuotaBudget(),
    )
    assert page.next_page_token == "N"
    assert len(page.items) == 1
