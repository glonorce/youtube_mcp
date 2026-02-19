"""Unit tests for video_classification."""

from __future__ import annotations

from src.youtube_mcp.video_classification import is_live, is_short, parse_duration_seconds


def test_parse_duration_seconds() -> None:
    assert parse_duration_seconds("PT30S") == 30
    assert parse_duration_seconds("PT5M") == 300
    assert parse_duration_seconds("PT1H2M3S") == 3723
    assert parse_duration_seconds("bogus") is None


def test_is_short() -> None:
    v = {"contentDetails": {"duration": "PT30S"}}
    assert is_short(v) is True
    v2 = {"contentDetails": {"duration": "PT5M"}}
    assert is_short(v2) is False


def test_is_live() -> None:
    v = {"snippet": {"liveBroadcastContent": "live"}}
    assert is_live(v) is True
    v2 = {"snippet": {"liveBroadcastContent": "none"}}
    assert is_live(v2) is False
