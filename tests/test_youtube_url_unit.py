"""Unit tests for youtube_url.extract_video_id."""

from __future__ import annotations

import pytest

from src.youtube_mcp.youtube_url import extract_video_id


def test_extract_video_id_from_watch_url() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_from_short_url() -> None:
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_from_shorts_url() -> None:
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_accepts_raw_id() -> None:
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        extract_video_id("not a url")
