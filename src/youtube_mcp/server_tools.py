"""youtube_mcp.server_tools

Intent:
    MCP tool wrapper functions with rich, AI-friendly docstrings.

Why:
    - Keep server bootstrap small (SoC, <100 lines target).
    - Ensure tool contracts are self-describing for LLM clients.

Conventions:
    - Tool wrappers must be thin: validate inputs, call domain/tool-handlers, and
      return structured JSON objects.
    - Any potentially expensive behavior must be explicit opt-in and documented.
"""

from __future__ import annotations

from typing import Any

from .mcp_tools_channel import resolve_youtube_channel_tool
from .mcp_tools_channel_playlists import list_youtube_channel_playlists_tool
from .mcp_tools_channel_videos import list_youtube_channel_videos_tool
from .mcp_tools_playlist_videos import list_youtube_playlist_videos_tool
from .mcp_tools_channel_search import search_youtube_channel_videos_tool
from .mcp_tools_video_comments import list_youtube_video_comments_tool


def resolve_youtube_channel(
    channel_ref: str,
    resolution_mode: str = "strict",
    include_uploads_playlist: bool = True,
) -> dict[str, Any]:
    """Resolve a YouTube channel reference into a concrete channelId.

    What this tool does:
        - Converts a user-facing channel identifier into a YouTube `channelId`.
        - Optionally returns the channel's `uploadsPlaylistId`, which enables
          listing *all* uploaded videos via playlistItems.list.

    Supported input formats (examples):
        - Handle: `@GoogleDevelopers`
        - Handle URL: `https://www.youtube.com/@GoogleDevelopers`
        - Channel ID URL: `https://www.youtube.com/channel/UC...`
        - Legacy username URL: `https://www.youtube.com/user/SomeUsername`

    Parameters:
        channel_ref:
            Channel identifier in one of the supported formats.
        resolution_mode:
            - `strict` (default): ambiguous inputs are rejected with an
              explainable error. This prevents "silent wrong channel" bugs.
            - `best_effort`: ambiguous inputs return a short list of candidate
              channels. (This mode may use the Search API and can be expensive.)
        include_uploads_playlist:
            If true, attempts to include `uploadsPlaylistId` in the output.

    Returns (structured JSON):
        - channelId: string | null
        - title: string | null
        - handle: string | null
        - uploadsPlaylistId: string | null
        - warnings: string[]
        - candidates: {channelId,title,handle}[]

    Failure modes:
        - Missing API key: raises error "YOUTUBE_API_KEY not configured".
        - Ambiguous/unsupported input (strict): raises ValueError with guidance.

    Safety notes:
        - Does not perform destructive actions.
        - Does not access private channel data.
    """

    return resolve_youtube_channel_tool(
        channel_ref=channel_ref,
        resolution_mode=resolution_mode,  # type: ignore[arg-type]
        include_uploads_playlist=include_uploads_playlist,
    )


def list_youtube_channel_videos(
    channel_ref: str,
    max_videos: int = 200,
    page_token: str | None = None,
    next_page_token: str | None = None,
    include_shorts: bool = False,
    include_live: bool = False,
    parts_level: str = "basic",
    order_strategy: str = "uploads_playlist",
    order_by: str = "date",
) -> dict[str, Any]:
    """List videos for a channel (public data), with safe defaults.

    Default behavior (safe + complete):
        - Uses the channel's uploads playlist (`uploadsPlaylistId`) to paginate
          through *all* uploaded videos.

    Parameters:
        channel_ref:
            Same formats as `resolve_youtube_channel`.
        max_videos:
            Hard limit per tool call. The tool may return fewer items and set
            `truncated=true`.
        page_token:
            Token for pagination (from previous response `nextPageToken`).
            Alias: you may also pass `next_page_token` (some agents prefer it).
        include_shorts:
            Default false. If true, includes Shorts (best-effort classification).
        include_live:
            Default false. If true, includes live/upcoming videos (best-effort).
        parts_level:
            - `basic` (default): snippet + statistics + contentDetails
            - `full`: also requests status/liveStreamingDetails (heavier payload)
        order_strategy:
            - `uploads_playlist` (default): low quota, paginated.
            - `local_sort`: fetches a bounded subset then sorts locally.
              (Not paginated; `page_token` must be null.)
            - `search_api`: uses YouTube Search API ordering (expensive, capped).
              Explicit opt-in only.
        order_by:
            - `date` (default)
            - `viewCount`, `likeCount`, `commentCount`, `duration`
            Note: `search_api` supports only `date` and `viewCount`.

    Returns (structured JSON):
        - items: video[] (YouTube API video resources)
        - nextPageToken: string | null
        - next_page_token: string | null  (alias of nextPageToken for agent friendliness)
        - quotaEstimate: {estimatedUnits,strategy,notes[]}
        - truncated: bool
        - appliedMaxVideos: int
        - appliedOrder: {strategy, by}

    Quota/performance notes:
        - Search API calls are expensive (quota ~100/unit per call) and may be
          capped for channels.
        - local_sort is bounded by max_videos and max_pages.

    Safety notes:
        - Public data only; no private playlists/videos.
        - No file/network access except YouTube Data API endpoints.
    """

    return list_youtube_channel_videos_tool(
        channel_ref=channel_ref,
        max_videos=max_videos,
        page_token=page_token,
        next_page_token=next_page_token,
        include_shorts=include_shorts,
        include_live=include_live,
        parts_level=parts_level,  # type: ignore[arg-type]
        order_strategy=order_strategy,  # type: ignore[arg-type]
        order_by=order_by,  # type: ignore[arg-type]
    )


def search_youtube_channel_videos(
    channel_ref: str,
    query: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
    max_videos: int = 50,
    include_shorts: bool = False,
    include_live: bool = False,
    parts_level: str = "basic",
    order: str = "relevance",
) -> dict[str, Any]:
    """Search for videos within a channel by keyword (public data).

    When to use:
        Use this tool when you want to find videos by **keyword** without
        enumerating the full uploads playlist.

    Important:
        - This tool uses the YouTube **Search API** (`search.list`).
        - Search is **quota-expensive** (about **100 units per page**).
        - Results may be capped by YouTube API behavior for channel searches.

    Pagination:
        - Read `nextPageToken` (or `next_page_token`) from the response.
        - Pass it back as `page_token` (or `next_page_token`) to fetch the next page.

    Returns:
        - items: hydrated video resources (`videos.list`)
        - nextPageToken / next_page_token
        - quotaEstimate
    """

    return search_youtube_channel_videos_tool(
        channel_ref=channel_ref,
        query=query,
        page_token=page_token,
        next_page_token=next_page_token,
        max_videos=max_videos,
        include_shorts=include_shorts,
        include_live=include_live,
        parts_level=parts_level,  # type: ignore[arg-type]
        order=order,  # type: ignore[arg-type]
    )


def list_youtube_channel_playlists(
    channel_ref: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
) -> dict[str, Any]:
    """List public playlists for a channel.

    Parameters:
        channel_ref:
            Same formats as `resolve_youtube_channel`.
        page_token:
            Token for pagination.

    Returns:
        - items: playlist[] (YouTube API playlist resources)
        - nextPageToken: string | null
        - quotaEstimate: {estimatedUnits,strategy,notes[]}

    Notes:
        - Public playlists only.
        - This tool does not list "private" playlists.
    """

    return list_youtube_channel_playlists_tool(
        channel_ref=channel_ref,
        page_token=page_token,
        next_page_token=next_page_token,
    )


def list_youtube_video_comments(
    video_id: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
    max_threads: int = 100,
    order: str = "relevance",
    text_format: str = "plainText",
    include_replies: bool = False,
) -> dict[str, Any]:
    """List comment threads for a YouTube video (public comments).

    Notes:
        - Uses `commentThreads.list` (quota cost ~1 per page).
        - `max_threads` is capped to 100 by the API.

    Pagination:
        - Response returns `nextPageToken` and `next_page_token`.
        - Pass it back as `page_token` (or `next_page_token`) to fetch the next page.

    Returns:
        - items: commentThread[] (includes top-level comment; replies optional)
        - nextPageToken / next_page_token
        - quotaEstimate

    Common failure:
        - If comments are disabled, YouTube may return 403 (commentsDisabled).
    """

    return list_youtube_video_comments_tool(
        video_id=video_id,
        page_token=page_token,
        next_page_token=next_page_token,
        max_threads=max_threads,
        order=order,  # type: ignore[arg-type]
        text_format=text_format,  # type: ignore[arg-type]
        include_replies=include_replies,
    )


def list_youtube_playlist_videos(
    playlist_id: str,
    page_token: str | None = None,
    next_page_token: str | None = None,
    max_items: int = 50,
    include_shorts: bool = False,
    include_live: bool = False,
    parts_level: str = "basic",
) -> dict[str, Any]:
    """List videos in a playlist (public data).

    Parameters:
        playlist_id:
            YouTube playlist ID (e.g. `PL...`).
        page_token:
            Token for pagination.
        max_items:
            Max number of items to include from this page.
        include_shorts/include_live:
            Default false; best-effort classification.
        parts_level:
            basic/full (same meaning as channel videos).

    Returns:
        - items: video[]
        - nextPageToken: string | null
        - quotaEstimate: {estimatedUnits,strategy,notes[]}

    Notes:
        - Playlist ordering is YouTube's playlist ordering.
    """

    return list_youtube_playlist_videos_tool(
        playlist_id=playlist_id,
        page_token=page_token,
        next_page_token=next_page_token,
        max_items=max_items,
        include_shorts=include_shorts,
        include_live=include_live,
        parts_level=parts_level,  # type: ignore[arg-type]
    )
