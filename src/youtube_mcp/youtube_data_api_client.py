"""youtube_mcp.youtube_data_api_client

Intent:
    Production-grade YouTube Data API v3 client implementation.

Key properties:
    - Secure by default: fixed scheme/host/base-path and endpoint allowlist.
    - Zero-trust input: query params are strictly encoded and validated.
    - Resilient: bounded retries with exponential backoff for transient failures.
    - No secret leakage: API key is never logged or included in exception messages.

Non-goals:
    - OAuth flows (API key only for public data).
"""

from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .logger import get_logger
from .youtube_data_api_constants import (
    DEFAULT_HTTP_TIMEOUT_S,
    DEFAULT_INITIAL_BACKOFF_S,
    DEFAULT_MAX_BACKOFF_S,
    DEFAULT_MAX_RETRIES,
    YOUTUBE_DATA_API_ALLOWED_ENDPOINTS,
    YOUTUBE_DATA_API_BASE_PATH,
    YOUTUBE_DATA_API_HOST,
    YOUTUBE_DATA_API_SCHEME,
)
from .youtube_errors import (
    YouTubeApiAuthError,
    YouTubeApiBadRequestError,
    YouTubeApiError,
    YouTubeApiErrorContext,
    YouTubeApiMisconfigurationError,
    YouTubeApiNotFoundError,
    YouTubeApiQuotaExceededError,
    YouTubeApiTransientError,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class YouTubeDataApiClientConfig:
    api_key: str
    timeout_s: float = DEFAULT_HTTP_TIMEOUT_S
    max_retries: int = DEFAULT_MAX_RETRIES
    initial_backoff_s: float = DEFAULT_INITIAL_BACKOFF_S
    max_backoff_s: float = DEFAULT_MAX_BACKOFF_S


class YouTubeDataApiClient:
    """Concrete IYouTubeClient implementation using urllib (stdlib)."""

    def __init__(self, config: YouTubeDataApiClientConfig):
        if not config.api_key or not config.api_key.strip():
            raise YouTubeApiMisconfigurationError("YouTube API key is required")

        self._config = config

    # ---- Public methods (IYouTubeClient surface)
    def channels_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        return self._get("channels", part=part, params=params)

    def playlists_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        return self._get("playlists", part=part, params=params)

    def playlist_items_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        return self._get("playlistItems", part=part, params=params)

    def videos_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        return self._get("videos", part=part, params=params)

    def search_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        return self._get("search", part=part, params=params)

    def comment_threads_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        return self._get("commentThreads", part=part, params=params)

    # ---- Internal
    def _get(self, endpoint: str, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        # ---- ADIM 1 — Intent (micro_decision_protocol)
        # Perform a safe GET request to a YouTube Data API v3 endpoint with retries.

        if endpoint not in YOUTUBE_DATA_API_ALLOWED_ENDPOINTS:
            raise YouTubeApiMisconfigurationError(f"Endpoint is not allowlisted: {endpoint}")

        if not part or not part.strip():
            raise YouTubeApiBadRequestError("'part' parameter is required")

        query = self._build_query(part=part, params=params)
        url = self._build_url(endpoint=endpoint, query=query)

        # Approach validation: ADR-004 (stdlib urllib, fixed host allowlist) ✅
        return self._request_json(url=url, endpoint=endpoint)

    def _build_url(self, *, endpoint: str, query: str) -> str:
        # Fixed host/scheme/base path: SSRF guardrail.
        path = f"{YOUTUBE_DATA_API_BASE_PATH}/{endpoint}"
        return urllib.parse.urlunparse(
            (YOUTUBE_DATA_API_SCHEME, YOUTUBE_DATA_API_HOST, path, "", query, "")
        )

    def _build_query(self, *, part: str, params: Mapping[str, str]) -> str:
        # Always inject API key and part.
        q: dict[str, str] = {"key": self._config.api_key, "part": part}
        for k, v in params.items():
            if v is None:
                continue
            q[str(k)] = str(v)

        # urlencode will percent-encode safely.
        return urllib.parse.urlencode(q, doseq=False, safe=",")

    def _request_json(self, *, url: str, endpoint: str) -> dict[str, Any]:
        attempt = 0
        backoff = self._config.initial_backoff_s

        while True:
            attempt += 1
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "Accept": "application/json",
                        # Gzip optional; urllib transparently handles if server responds.
                        "Accept-Encoding": "gzip",
                        "User-Agent": "youtube_mcp (gzip)",
                    },
                )

                with urllib.request.urlopen(req, timeout=self._config.timeout_s) as resp:
                    body = resp.read()

                    # Some environments return gzip-compressed bodies even though
                    # the response is JSON. Detect via header and (as a fallback)
                    # the gzip magic bytes (0x1f, 0x8b).
                    encoding = None
                    try:
                        encoding = resp.headers.get("Content-Encoding")
                    except Exception:
                        encoding = None

                    if (isinstance(encoding, str) and encoding.lower() == "gzip") or (
                        len(body) >= 2 and body[0] == 0x1F and body[1] == 0x8B
                    ):
                        try:
                            body = gzip.decompress(body)
                        except Exception as e:
                            raise YouTubeApiError(
                                "Failed to decompress YouTube API response",
                                context=YouTubeApiErrorContext(
                                    endpoint=endpoint,
                                    http_status=getattr(resp, "status", None),
                                    reason="gzip_decompress_failed",
                                    request_id=resp.headers.get("X-Request-Id"),
                                ),
                            ) from e

                    # We expect JSON
                    try:
                        return json.loads(body.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        raise YouTubeApiError(
                            "Invalid JSON response from YouTube API",
                            context=YouTubeApiErrorContext(
                                endpoint=endpoint,
                                http_status=getattr(resp, "status", None),
                                reason="invalid_json",
                                request_id=resp.headers.get("X-Request-Id"),
                            ),
                        ) from e

            except urllib.error.HTTPError as e:
                # NOTE: Do not include full URL (contains API key) in error.
                status = int(getattr(e, "code", 0) or 0)
                reason = _safe_extract_reason(e)

                # Classify
                if status == 400:
                    raise YouTubeApiBadRequestError(
                        "YouTube API rejected the request (400)",
                        context=YouTubeApiErrorContext(endpoint, status, reason, None),
                    ) from None
                if status in {401, 403}:
                    # quotaExceeded is a common 403 reason.
                    if reason == "quotaExceeded":
                        raise YouTubeApiQuotaExceededError(
                            "YouTube API quota exceeded",
                            context=YouTubeApiErrorContext(endpoint, status, reason, None),
                        ) from None
                    raise YouTubeApiAuthError(
                        "YouTube API authorization failed",
                        context=YouTubeApiErrorContext(endpoint, status, reason, None),
                    ) from None
                if status == 404:
                    raise YouTubeApiNotFoundError(
                        "YouTube API resource not found",
                        context=YouTubeApiErrorContext(endpoint, status, reason, None),
                    ) from None

                # Retryable: 429 or 5xx
                if status == 429 or 500 <= status <= 599:
                    if attempt <= self._config.max_retries:
                        logger.warning(
                            "Transient YouTube API HTTP error; retrying",
                            extra={"endpoint": endpoint, "status": status, "attempt": attempt, "reason": reason},
                        )
                        time.sleep(backoff)
                        backoff = min(backoff * 2.0, self._config.max_backoff_s)
                        continue

                    raise YouTubeApiTransientError(
                        "YouTube API transient error (retries exhausted)",
                        context=YouTubeApiErrorContext(endpoint, status, reason, None),
                    ) from None

                # Anything else: fail-fast.
                raise YouTubeApiError(
                    "YouTube API request failed",
                    context=YouTubeApiErrorContext(endpoint, status, reason, None),
                ) from None

            except (urllib.error.URLError, TimeoutError) as e:
                if attempt <= self._config.max_retries:
                    logger.warning(
                        "Network error calling YouTube API; retrying",
                        extra={"endpoint": endpoint, "attempt": attempt, "error": type(e).__name__},
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2.0, self._config.max_backoff_s)
                    continue

                raise YouTubeApiTransientError(
                    "Network error calling YouTube API (retries exhausted)",
                    context=YouTubeApiErrorContext(endpoint, None, type(e).__name__, None),
                ) from None


def _safe_extract_reason(err: urllib.error.HTTPError) -> str | None:
    """Try to extract YouTube error reason without leaking secrets.

    The YouTube error response body is JSON and may include:
        error.errors[0].reason

    This function must never raise.
    """

    try:
        body = err.read()
        data = json.loads(body.decode("utf-8"))
        errors = data.get("error", {}).get("errors", [])
        if errors and isinstance(errors, list):
            reason = errors[0].get("reason")
            if isinstance(reason, str):
                return reason
        return None
    except Exception:
        return None
