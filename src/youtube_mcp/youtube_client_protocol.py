"""youtube_mcp.youtube_client_protocol

Intent:
    Define strict contracts (interfaces) for interacting with YouTube Data API.

Design choice:
    - Use `typing.Protocol` to enable dependency inversion without forcing
      concrete inheritance.
    - This keeps the domain layer platform-agnostic and test-friendly.

Non-goals:
    - No HTTP logic here.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class IYouTubeClient(Protocol):
    """Interface for YouTube Data API operations used by this project.

    Notes:
        - Implementations must be deterministic and safe-by-default.
        - All methods must raise `YouTubeApiError` (or subclasses) for API-level
          failures.
    """

    def channels_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def playlists_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def playlist_items_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def videos_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def search_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def comment_threads_list(self, *, part: str, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError
