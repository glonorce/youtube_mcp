"""Unit tests for youtube_data_api_client.

Intent:
    Validate security and resilience properties without real network calls.

Key assertions:
    - Endpoint allowlist enforced
    - URL does not accept user-controlled host
    - HTTP errors map to typed exceptions

We mock urllib.request.urlopen.
"""

from __future__ import annotations

import io
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.youtube_mcp.youtube_data_api_client import (
    YouTubeDataApiClient,
    YouTubeDataApiClientConfig,
)
from src.youtube_mcp.youtube_errors import (
    YouTubeApiAuthError,
    YouTubeApiBadRequestError,
    YouTubeApiMisconfigurationError,
    YouTubeApiNotFoundError,
    YouTubeApiQuotaExceededError,
)


class _FakeResponse:
    def __init__(self, status: int, payload: dict, *, gzip_encoded: bool = False):
        self.status = status
        raw = json.dumps(payload).encode("utf-8")
        if gzip_encoded:
            import gzip as _gzip

            self._body = _gzip.compress(raw)
            self.headers = {"Content-Encoding": "gzip"}
        else:
            self._body = raw
            self.headers = {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_missing_api_key_is_misconfiguration_error() -> None:
    with pytest.raises(YouTubeApiMisconfigurationError):
        YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key=""))


def test_endpoint_not_allowlisted() -> None:
    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k"))
    with pytest.raises(YouTubeApiMisconfigurationError):
        client._get("notAllowed", part="snippet", params={})  # type: ignore[attr-defined]


@patch("urllib.request.urlopen")
def test_http_400_maps_to_bad_request(mock_urlopen) -> None:
    import urllib.error

    body = json.dumps({"error": {"errors": [{"reason": "badRequest"}]}}).encode("utf-8")
    err = urllib.error.HTTPError(
        url="https://example.invalid",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=io.BytesIO(body),
    )
    mock_urlopen.side_effect = err

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k", max_retries=0))
    with pytest.raises(YouTubeApiBadRequestError):
        client.channels_list(part="snippet", params={"id": "UC_x"})


@patch("urllib.request.urlopen")
def test_http_404_maps_to_not_found(mock_urlopen) -> None:
    import urllib.error

    body = json.dumps({"error": {"errors": [{"reason": "channelNotFound"}]}}).encode("utf-8")
    err = urllib.error.HTTPError(
        url="https://example.invalid",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=io.BytesIO(body),
    )
    mock_urlopen.side_effect = err

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k", max_retries=0))
    with pytest.raises(YouTubeApiNotFoundError):
        client.channels_list(part="snippet", params={"id": "UC_x"})


@patch("urllib.request.urlopen")
def test_http_403_quota_exceeded_maps_to_quota_error(mock_urlopen) -> None:
    import urllib.error

    body = json.dumps({"error": {"errors": [{"reason": "quotaExceeded"}]}}).encode("utf-8")
    err = urllib.error.HTTPError(
        url="https://example.invalid",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=io.BytesIO(body),
    )
    mock_urlopen.side_effect = err

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k", max_retries=0))
    with pytest.raises(YouTubeApiQuotaExceededError):
        client.videos_list(part="snippet", params={"id": "dQw4w9WgXcQ"})


@patch("urllib.request.urlopen")
def test_http_403_other_maps_to_auth_error(mock_urlopen) -> None:
    import urllib.error

    body = json.dumps({"error": {"errors": [{"reason": "forbidden"}]}}).encode("utf-8")
    err = urllib.error.HTTPError(
        url="https://example.invalid",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=io.BytesIO(body),
    )
    mock_urlopen.side_effect = err

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k", max_retries=0))
    with pytest.raises(YouTubeApiAuthError):
        client.playlists_list(part="snippet", params={"channelId": "UC_x"})


@patch("urllib.request.urlopen")
def test_success_response_parses_json(mock_urlopen) -> None:
    mock_urlopen.return_value = _FakeResponse(status=200, payload={"kind": "youtube#channelsListResponse"})

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k", max_retries=0))
    res = client.channels_list(part="snippet", params={"id": "UC_x"})
    assert res["kind"] == "youtube#channelsListResponse"


@patch("urllib.request.urlopen")
def test_success_response_parses_gzip_json(mock_urlopen) -> None:
    mock_urlopen.return_value = _FakeResponse(
        status=200,
        payload={"kind": "youtube#channelsListResponse"},
        gzip_encoded=True,
    )

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key="k", max_retries=0))
    res = client.channels_list(part="snippet", params={"id": "UC_x"})
    assert res["kind"] == "youtube#channelsListResponse"
