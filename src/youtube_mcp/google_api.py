"""youtube_mcp.google_api

Intent:
    Video info extraction adapter.

Design constraints:
    - The package must remain importable even when optional extractor
      dependencies are not installed.
    - Fail-fast when the functionality is invoked without dependencies.

Notes:
    - Today this uses `yt_info_extract.get_video_info(video_id)`.
    - API key is accepted for forward compatibility, but the current extractor
      does not require it.
"""

from __future__ import annotations

from typing import Any, Callable

from .logger import get_logger

logger = get_logger(__name__)


# Optional dependency (do not raise at import-time).
try:
    from yt_info_extract import get_video_info as yt_get_video_info  # type: ignore
except ModuleNotFoundError:
    yt_get_video_info: Callable[[str], dict[str, Any] | None] | None = None


def get_video_info(api_key: str | None, video_id: str) -> dict[str, Any] | None:
    """Fetch detailed information about a YouTube video.

    Args:
        api_key: YouTube Data API v3 key (kept for compatibility/forward use).
        video_id: The YouTube video ID.

    Returns:
        Video information dict, or None if not found.

    Raises:
        RuntimeError: if optional extractor dependency is not installed.
    """

    if yt_get_video_info is None:
        raise RuntimeError(
            "yt_info_extract is not installed; cannot fetch video info. "
            "Install project dependencies to enable this capability."
        )

    try:
        logger.info("Fetching video info", extra={"video_id": video_id})
        video_info = yt_get_video_info(video_id)

        if not video_info:
            logger.warning("Video not found", extra={"video_id": video_id})
            return None

        logger.info(
            "Successfully fetched video info",
            extra={"video_id": video_id, "title": video_info.get("title", "Unknown")},
        )
        return video_info

    except Exception as e:
        logger.error("Video info extraction error", extra={"video_id": video_id, "error": str(e)})
        return None


def format_video_info(video_info: dict[str, Any] | None) -> str:
    """Format video information into a readable string."""

    if not video_info:
        logger.debug("No video info to format")
        return "Video not found or unavailable."

    result: list[str] = [
        f"Title: {video_info.get('title', 'N/A')}",
        f"Channel: {video_info.get('channel_name', 'N/A')}",
        f"Published: {video_info.get('publication_date', 'N/A')}",
        (f"Views: {video_info.get('views', 'N/A'):,}" if video_info.get("views") else "Views: N/A"),
        f"Description: {video_info.get('description', 'N/A')}",
    ]

    formatted_info = "\n".join(result)
    logger.debug("Formatted video info", extra={"length": len(formatted_info)})
    return formatted_info
