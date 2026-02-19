"""youtube_mcp.youtube_errors

Intent:
    Centralized, typed error model for YouTube Data API interactions.

Why:
    - Fail-fast and predictable error propagation.
    - Avoid leaking sensitive data (API key, full URLs) through exception messages.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class YouTubeApiErrorContext:
    endpoint: str
    http_status: int | None
    reason: str | None
    request_id: str | None


class YouTubeApiError(RuntimeError):
    """Base error for all YouTube API client failures."""

    def __init__(self, message: str, *, context: YouTubeApiErrorContext | None = None):
        super().__init__(message)
        self.context = context


class YouTubeApiQuotaExceededError(YouTubeApiError):
    """Raised when API quota is exceeded."""


class YouTubeApiAuthError(YouTubeApiError):
    """Raised for authentication/authorization failures."""


class YouTubeApiBadRequestError(YouTubeApiError):
    """Raised for invalid parameters or request shape errors."""


class YouTubeApiNotFoundError(YouTubeApiError):
    """Raised when a resource cannot be found."""


class YouTubeApiTransientError(YouTubeApiError):
    """Raised for retryable failures (429, 5xx, network)."""


class YouTubeApiMisconfigurationError(YouTubeApiError):
    """Raised when the client is misconfigured (missing API key, invalid endpoint)."""
