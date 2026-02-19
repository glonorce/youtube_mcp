"""youtube_mcp.youtube_data_api_constants

Intent:
    Single Source of Truth (SSOT) for YouTube Data API v3 client constants.

Security posture:
    - HTTP requests must target a fixed, allowlisted host.
    - Endpoints are selected from an explicit allowlist.
"""

from __future__ import annotations

from typing import Final


YOUTUBE_DATA_API_HOST: Final[str] = "www.googleapis.com"
YOUTUBE_DATA_API_BASE_PATH: Final[str] = "/youtube/v3"
YOUTUBE_DATA_API_SCHEME: Final[str] = "https"

# SSOT: Endpoints this project is allowed to call.
# (Keep this list tight; expand only with ADR updates.)
YOUTUBE_DATA_API_ALLOWED_ENDPOINTS: Final[frozenset[str]] = frozenset(
    {
        "channels",
        "playlists",
        "playlistItems",
        "videos",
        "search",  # allowed but must remain opt-in at higher layers
        "commentThreads",
    }
)

# Networking defaults
DEFAULT_HTTP_TIMEOUT_S: Final[float] = 10.0
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_INITIAL_BACKOFF_S: Final[float] = 0.5
DEFAULT_MAX_BACKOFF_S: Final[float] = 4.0

# API defaults
DEFAULT_MAX_RESULTS: Final[int] = 50  # YouTube Data API list endpoints: 0..50
