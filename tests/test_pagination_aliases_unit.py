"""Unit tests for pagination aliases.

Intent:
    Ensure tools return both nextPageToken and next_page_token, and accept
    next_page_token as an alias for page_token.

These tests do not require network access.
"""

from __future__ import annotations

import pytest

from src.youtube_mcp.mcp_tools_channel_playlists import list_youtube_channel_playlists_tool
from src.youtube_mcp.mcp_tools_channel_videos import list_youtube_channel_videos_tool
from src.youtube_mcp.mcp_tools_playlist_videos import list_youtube_playlist_videos_tool


class _FakeClient:
    def __init__(self):
        self.last_page_token = None

    def channels_list(self, *, part: str, params):
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
        self.last_page_token = params.get("pageToken")
        return {"items": [{"snippet": {"resourceId": {"videoId": "v1"}}}], "nextPageToken": "NEXT"}

    def videos_list(self, *, part: str, params):
        return {
            "items": [
                {
                    "id": "v1",
                    "snippet": {"liveBroadcastContent": "none"},
                    "contentDetails": {"duration": "PT5M"},
                    "statistics": {"viewCount": "1"},
                }
            ]
        }

    def playlists_list(self, *, part: str, params):
        self.last_page_token = params.get("pageToken")
        return {"items": [{"id": "PL_x"}], "nextPageToken": "NEXT"}

    def search_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def comment_threads_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "k")


def test_channel_videos_returns_alias_fields(monkeypatch):
    from src.youtube_mcp import mcp_tools_channel_videos as mod

    monkeypatch.setattr(mod, "YouTubeDataApiClient", lambda *_args, **_kw: _FakeClient())

    out = list_youtube_channel_videos_tool(channel_ref="@H", max_videos=1)
    assert out["nextPageToken"] == "NEXT"
    assert out["next_page_token"] == "NEXT"


def test_channel_videos_accepts_next_page_token_alias(monkeypatch):
    from src.youtube_mcp import mcp_tools_channel_videos as mod

    fake = _FakeClient()
    monkeypatch.setattr(mod, "YouTubeDataApiClient", lambda *_args, **_kw: fake)

    _ = list_youtube_channel_videos_tool(channel_ref="@H", max_videos=1, next_page_token="P")
    assert fake.last_page_token == "P"


def test_channel_playlists_returns_alias_fields(monkeypatch):
    from src.youtube_mcp import mcp_tools_channel_playlists as mod

    monkeypatch.setattr(mod, "YouTubeDataApiClient", lambda *_args, **_kw: _FakeClient())

    out = list_youtube_channel_playlists_tool(channel_ref="@H")
    assert out["nextPageToken"] == "NEXT"
    assert out["next_page_token"] == "NEXT"


def test_playlist_videos_returns_alias_fields(monkeypatch):
    from src.youtube_mcp import mcp_tools_playlist_videos as mod

    monkeypatch.setattr(mod, "YouTubeDataApiClient", lambda *_args, **_kw: _FakeClient())

    out = list_youtube_playlist_videos_tool(playlist_id="PL_x", max_items=1)
    assert out["nextPageToken"] == "NEXT"
    assert out["next_page_token"] == "NEXT"
