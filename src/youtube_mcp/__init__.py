"""youtube_mcp package.

Intent:
    Expose a small, stable public API while keeping import-time side effects and
    optional dependencies under strict control.

Why this matters (Production + Tests):
    - Importing this package should not require the MCP runtime (`mcp`) unless
      the server entrypoint is invoked.
    - Importing this package should not require optional extractors
      (`yt_info_extract`, `yt_ts_extract`) unless those capabilities are called.

This is critical for:
    - unit tests (fast, dependency-light)
    - static analysis
    - any consumer importing only a subset of functionality
"""

from __future__ import annotations

from typing import Any, Final

from .logger import get_logger

logger = get_logger(__name__)

__version__: Final[str] = "2.0.0"


# ----------------------------
# Lazy public API wrappers
# ----------------------------

def get_video_info(api_key: str | None, video_id: str) -> dict[str, Any] | None:
    """Lazy wrapper around google_api.get_video_info.

    Raises a clear error if optional dependencies are missing.
    """

    try:
        from .google_api import get_video_info as _get_video_info
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Optional dependency for video info extraction is missing. "
            "Install project dependencies to use get_video_info()."
        ) from e

    return _get_video_info(api_key, video_id)


def format_video_info(video_info: dict[str, Any]) -> str:
    """Lazy wrapper around google_api.format_video_info."""

    from .google_api import format_video_info as _format_video_info

    return _format_video_info(video_info)


def get_video_transcript(video_id: str) -> str | None:
    """Lazy wrapper around transcript_api.get_video_transcript."""

    try:
        from .transcript_api import get_video_transcript as _get_video_transcript
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Optional dependency for transcript extraction is missing. "
            "Install project dependencies to use get_video_transcript()."
        ) from e

    return _get_video_transcript(video_id)


# ----------------------------
# Optional MCP server exports
# ----------------------------

try:
    from .server import main, mcp  # noqa: F401
except ModuleNotFoundError as e:
    if e.name != "mcp":
        raise

    mcp = None  # type: ignore[assignment]

    def main() -> None:  # type: ignore[no-redef]
        raise RuntimeError(
            "MCP runtime dependency is not available. Install project dependencies "
            "to run the MCP server entrypoint."
        )


logger.info(f"YouTube MCP package initialized, version: {__version__}")

__all__ = [
    "mcp",
    "main",
    "get_video_info",
    "get_video_transcript",
    "format_video_info",
]
