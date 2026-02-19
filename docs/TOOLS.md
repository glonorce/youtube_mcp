# Tools & Actions Reference (youtube_mcp)

This document is a canonical reference for **all MCP tools** exposed by this server.

> Terminology note:
> - MCP "tools" are sometimes called "actions" by hosts.
> - This project exposes tools via `FastMCP.add_tool(...)` with rich docstrings.

---

## Global requirements

### Authentication
Most tools require:

- `YOUTUBE_API_KEY` (YouTube Data API v3 API key)

### Pagination conventions (IMPORTANT)
Many tools are **paginated**.

- Response includes:
  - `nextPageToken` (canonical, YouTube-style)
  - `next_page_token` (alias for agent friendliness)

- Request accepts:
  - `page_token`
  - `next_page_token` (alias)

Rule:
- If the response returns a non-null token, call the **same tool** again and pass
  that token as `page_token` (or `next_page_token`) to retrieve the next page.

---

## Tool: get_yt_video_info

Signature:
- `get_yt_video_info(video_id_or_url: str) -> str`

Purpose:
- Extracts video metadata and transcript (when available).

Input:
- A raw 11-character video id (e.g. `dQw4w9WgXcQ`) **or** a full YouTube URL.

Output:
- A formatted string (human-readable text).

Notes:
- This tool is string-based output (not structured JSON).

---

## Tool: resolve_youtube_channel

Purpose:
- Resolve a channel reference (handle/URL) into a concrete `channelId`.

Key params:
- `channel_ref` (required)
- `resolution_mode`: `strict` (default) or `best_effort`
- `include_uploads_playlist`: bool

Output keys:
- `channelId`, `title`, `handle`, `uploadsPlaylistId`, `warnings`, `candidates`

---

## Tool: list_youtube_channel_videos (paginated)

Purpose:
- List channel videos using safe defaults.

Key params:
- `channel_ref` (required)
- `max_videos` (default 200)
- `page_token` / `next_page_token`
- `include_shorts`, `include_live`
- `parts_level`: `basic` (default) or `full`
- `order_strategy`: `uploads_playlist` (default), `local_sort`, `search_api`
- `order_by`: `date`, `viewCount`, `likeCount`, `commentCount`, `duration`

Output keys:
- `items`, `nextPageToken`, `next_page_token`, `quotaEstimate`, `truncated`, `appliedMaxVideos`, `appliedOrder`

---

## Tool: list_youtube_channel_playlists (paginated)

Purpose:
- List public playlists for a channel.

Key params:
- `channel_ref`
- `page_token` / `next_page_token`

Output keys:
- `items`, `nextPageToken`, `next_page_token`, `quotaEstimate`

---

## Tool: list_youtube_playlist_videos (paginated)

Purpose:
- List videos in a public playlist.

Key params:
- `playlist_id`
- `page_token` / `next_page_token`
- `max_items` (per page extraction cap; default 50)
- `include_shorts`, `include_live`
- `parts_level`

Output keys:
- `items`, `nextPageToken`, `next_page_token`, `quotaEstimate`

---

## Tool: search_youtube_channel_videos (paginated, quota-expensive)

Purpose:
- Keyword search within a channel using `search.list`.

Key params:
- `channel_ref`
- `query`
- `order`: `relevance`, `date`, `viewCount`, `rating`, `title`
- `page_token` / `next_page_token`

Quota:
- Uses Search API: **~100 units per page**.

Output keys:
- `items`, `nextPageToken`, `next_page_token`, `quotaEstimate`, `appliedOrder`

---

## Tool: list_youtube_video_comments (paginated)

Purpose:
- Fetch public comment threads for a video via `commentThreads.list`.

Key params:
- `video_id`
- `max_threads` (API cap 100)
- `order`: `time` or `relevance`
- `text_format`: `plainText` or `html`
- `include_replies`: bool
- `page_token` / `next_page_token`

Quota:
- `commentThreads.list` is typically **1 unit per page**.

Output keys:
- `items`, `nextPageToken`, `next_page_token`, `quotaEstimate`

---

## Quota quick reference (best-effort)

Official: https://developers.google.com/youtube/v3/determine_quota_cost

Common costs:
- `videos.list`: 1
- `playlistItems.list`: 1
- `playlists.list`: 1
- `channels.list`: 1
- `commentThreads.list`: 1
- `search.list`: 100
