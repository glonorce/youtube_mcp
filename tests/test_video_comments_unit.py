"""Unit tests for video_comments."""

from __future__ import annotations

from src.youtube_mcp.quota_budgeter import QuotaBudget
from src.youtube_mcp.video_comments import list_video_comment_threads_page


class _FakeClient:
    def comment_threads_list(self, *, part: str, params):
        assert params["videoId"] == "v"
        assert params["maxResults"] == "100"
        return {"items": [{"id": "c1"}], "nextPageToken": "NEXT"}

    def channels_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def playlists_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def playlist_items_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def videos_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def search_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_list_video_comment_threads_page() -> None:
    client = _FakeClient()
    page = list_video_comment_threads_page(
        client=client,
        video_id="v",
        page_token=None,
        max_threads=100,
        order="relevance",
        text_format="plainText",
        include_replies=False,
        budget=QuotaBudget(max_quota_units=1000),
    )

    assert page.next_page_token == "NEXT"
    assert len(page.items) == 1
