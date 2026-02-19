"""Unit tests for channel_resolver.

Intent:
    Validate strict vs best-effort behavior deterministically using a fake client.

No network calls.
"""

from __future__ import annotations

import pytest

from src.youtube_mcp.channel_resolver import (
    ChannelResolutionError,
    resolve_channel,
)


class _FakeClient:
    def __init__(self, *, channels_items=None, search_items=None):
        self._channels_items = channels_items or []
        self._search_items = search_items or []

    def channels_list(self, *, part: str, params):
        return {"items": self._channels_items}

    def search_list(self, *, part: str, params):
        return {"items": self._search_items}

    # Unused in these tests
    def playlists_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def playlist_items_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError

    def videos_list(self, *, part: str, params):  # pragma: no cover
        raise NotImplementedError


def test_strict_query_raises() -> None:
    client = _FakeClient()
    with pytest.raises(ChannelResolutionError):
        resolve_channel(client=client, channel_ref="Some Channel Name", mode="strict")


def test_strict_custom_url_raises() -> None:
    client = _FakeClient()
    with pytest.raises(ChannelResolutionError):
        resolve_channel(client=client, channel_ref="https://www.youtube.com/c/Foo", mode="strict")


def test_handle_resolves_to_channel_id_and_uploads_playlist() -> None:
    client = _FakeClient(
        channels_items=[
            {
                "id": "UC_x",
                "snippet": {"title": "T", "customUrl": "@Handle"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU_x"}},
            }
        ]
    )
    res = resolve_channel(client=client, channel_ref="@Handle", mode="strict")
    assert res.channel_id == "UC_x"
    assert res.uploads_playlist_id == "UU_x"


def test_best_effort_returns_candidates_only() -> None:
    client = _FakeClient(
        search_items=[
            {"id": {"channelId": "UC_1"}, "snippet": {"title": "A", "channelTitle": "A"}},
            {"id": {"channelId": "UC_2"}, "snippet": {"title": "B", "channelTitle": "B"}},
        ]
    )
    res = resolve_channel(client=client, channel_ref="Acme", mode="best_effort")
    assert res.channel_id == ""
    assert len(res.candidates) == 2
    assert res.warnings and "best_effort" in res.warnings[0]
