"""Unit tests for youtube_mcp.channel_ref.

Intent:
    Prove that channel reference parsing is deterministic, strict, and
    does not silently mis-classify ambiguous inputs.

Note:
    These tests do not perform any network calls.
"""

import pytest

from src.youtube_mcp.channel_ref import (
    ChannelRefParseError,
    parse_channel_ref,
)


@pytest.mark.parametrize(
    "raw, expected_kind, expected_value",
    [
        ("@GoogleDevelopers", "handle", "GoogleDevelopers"),
        (" @GoogleDevelopers ", "handle", "GoogleDevelopers"),
        ("https://www.youtube.com/@GoogleDevelopers", "handle", "GoogleDevelopers"),
        ("www.youtube.com/@GoogleDevelopers", "handle", "GoogleDevelopers"),
        ("https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw", "channel_id", "UC_x5XG1OV2P6uZZ5FSM9Ttw"),
        ("UC_x5XG1OV2P6uZZ5FSM9Ttw", "channel_id", "UC_x5XG1OV2P6uZZ5FSM9Ttw"),
        ("https://www.youtube.com/user/GoogleDevelopers", "username", "GoogleDevelopers"),
        ("https://www.youtube.com/c/GoogleDevelopers", "custom_url", "GoogleDevelopers"),
    ],
)
def test_parse_channel_ref_success(raw: str, expected_kind: str, expected_value: str) -> None:
    ref = parse_channel_ref(raw)
    assert ref.kind == expected_kind
    assert ref.value == expected_value
    assert ref.raw.strip() == raw.strip()


@pytest.mark.parametrize(
    "raw",
    [
        "",
        " ",
        "@",  # empty handle
        "https://evil.example.com/@GoogleDevelopers",  # non-youtube host should not be parsed as youtube
    ],
)
def test_parse_channel_ref_invalid_inputs(raw: str) -> None:
    if raw.startswith("https://evil.example.com"):
        # This should not raise; it should be treated as query.
        ref = parse_channel_ref(raw)
        assert ref.kind == "query"
        return

    with pytest.raises(ChannelRefParseError):
        parse_channel_ref(raw)


def test_parse_channel_ref_unknown_youtube_path_becomes_query() -> None:
    ref = parse_channel_ref("https://www.youtube.com/some/unknown/path")
    assert ref.kind == "query"
    assert "unknown" in ref.value
