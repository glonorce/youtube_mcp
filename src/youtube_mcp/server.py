"""youtube_mcp.server

Intent:
    MCP server bootstrap and tool registration.

Rules:
    - Keep this file small (SoC).
    - Preserve backward compatibility for `get_yt_video_info(video_id)`.

Tool contracts:
    Rich, AI-friendly tool docstrings live in `server_tools.py`.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .logger import get_logger
from .server_tools import (
    list_youtube_channel_playlists,
    list_youtube_channel_videos,
    list_youtube_playlist_videos,
    list_youtube_video_comments,
    resolve_youtube_channel,
    search_youtube_channel_videos,
)
from .youtube import format_video_info, get_video_info, get_video_transcript
from .youtube_url import extract_video_id

logger = get_logger(__name__)

mcp = FastMCP("YouTube Video Analyzer")


@mcp.tool()
def get_yt_video_info(video_id: str) -> str:
    """Fetch YouTube video information and transcript.

    Tip:
        You can pass either a raw video id (11 chars) or a full YouTube URL.
    """

    raw_input = video_id
    try:
        video_id = extract_video_id(video_id)
    except Exception:
        # Keep legacy behavior: if parsing fails, continue with raw value.
        video_id = raw_input

    logger.info("MCP tool called: get_yt_video_info", extra={"video_id": video_id})

    api_key = os.getenv("YOUTUBE_API_KEY", "")

    result: list[str] = []

    try:
        video_info = get_video_info(api_key, video_id)
        result.append("=== VIDEO INFORMATION ===")
        result.append(format_video_info(video_info))
        result.append("")

        transcript = get_video_transcript(video_id)
        result.append("=== TRANSCRIPT ===")
        if transcript and not transcript.startswith("Transcript error:") and not transcript.startswith("Could not retrieve"):
            result.append(transcript)
        else:
            if transcript and (transcript.startswith("Transcript error:") or transcript.startswith("Could not retrieve")):
                result.append(f"Transcript issue: {transcript}")
            else:
                result.append("No transcript available for this video.")

        final_result = "\n".join(result)
        logger.debug("Tool execution completed", extra={"video_id": video_id, "result_length": len(final_result)})
        return final_result

    except Exception as e:
        logger.error("Error processing video", extra={"video_id": video_id, "error": str(e)}, exc_info=True)
        return f"Error processing video {video_id}: {str(e)}"


# New tools (rich docstrings in server_tools.py)
# NOTE:
# - `FastMCP.tool(...)` is a decorator factory.
# - For programmatic registration, use `FastMCP.add_tool(fn=...)`.
# We also pass `description=fn.__doc__` to guarantee AI clients receive the rich
# tool docs.
mcp.add_tool(resolve_youtube_channel, description=resolve_youtube_channel.__doc__)
mcp.add_tool(list_youtube_channel_videos, description=list_youtube_channel_videos.__doc__)
mcp.add_tool(list_youtube_channel_playlists, description=list_youtube_channel_playlists.__doc__)
mcp.add_tool(list_youtube_playlist_videos, description=list_youtube_playlist_videos.__doc__)
mcp.add_tool(search_youtube_channel_videos, description=search_youtube_channel_videos.__doc__)
mcp.add_tool(list_youtube_video_comments, description=list_youtube_video_comments.__doc__)


def main() -> None:
    logger.info("Starting YouTube MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
