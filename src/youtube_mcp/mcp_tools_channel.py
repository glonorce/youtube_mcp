"""youtube_mcp.mcp_tools_channel

Intent:
    MCP tool handler(s) for channel resolution.

Notes:
    This module is pure application logic. Server bootstrap registers these
    handlers as MCP tools.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from .channel_resolver import ChannelResolutionError, ResolvedChannel, resolve_channel
from .youtube_data_api_client import YouTubeDataApiClient, YouTubeDataApiClientConfig


ResolutionMode = Literal["strict", "best_effort"]


def resolve_youtube_channel_tool(
    *,
    channel_ref: str,
    resolution_mode: ResolutionMode = "strict",
    include_uploads_playlist: bool = True,
) -> dict[str, Any]:
    """Tool handler: resolve a channel reference to a channelId + metadata."""

    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not configured")

    # Some MCP hosts do not expand placeholders like ${YOUTUBE_API_KEY} in config.
    # If the value looks like an unexpanded placeholder, fail-fast with guidance.
    if api_key.startswith("${") and api_key.endswith("}"):
        raise RuntimeError(
            "YOUTUBE_API_KEY appears to be an unexpanded placeholder (e.g. '${YOUTUBE_API_KEY}'). "
            "Your MCP host likely does not interpolate env vars inside mcp.json. "
            "Set YOUTUBE_API_KEY in the host process environment, use a .env + python -m pip install -e ., "
            "or paste the key directly in the MCP config."
        )

    client = YouTubeDataApiClient(YouTubeDataApiClientConfig(api_key=api_key))

    try:
        resolved: ResolvedChannel = resolve_channel(
            client=client,
            channel_ref=channel_ref,
            mode=resolution_mode,
            include_uploads_playlist=include_uploads_playlist,
        )
        return {
            "channelId": resolved.channel_id or None,
            "title": resolved.title,
            "handle": resolved.handle,
            "uploadsPlaylistId": resolved.uploads_playlist_id,
            "warnings": list(resolved.warnings),
            "candidates": [
                {"channelId": c.channel_id, "title": c.title, "handle": c.handle}
                for c in resolved.candidates
            ],
        }

    except ChannelResolutionError as e:
        raise ValueError(str(e))
