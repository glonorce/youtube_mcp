"""youtube_mcp.youtube_url

Intent:
    Parse common YouTube URL formats into a canonical `video_id`.

Why:
    Many MCP users will paste a full YouTube URL rather than a bare video id.

Supported examples:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://www.youtube.com/shorts/dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ

Non-goals:
    - Playlists and channel URLs (handled by other tools).
"""

from __future__ import annotations

import re
import urllib.parse


_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(value: str) -> str:
    """Extract a YouTube video id from a URL or return the id if already provided.

    Raises:
        ValueError: if no video id can be extracted.
    """

    if not value or not value.strip():
        raise ValueError("video url/id is required")

    s = value.strip()
    if _VIDEO_ID_RE.match(s):
        return s

    # Try to parse as URL
    try:
        u = urllib.parse.urlparse(s)
    except Exception as e:  # pragma: no cover
        raise ValueError("invalid URL") from e

    host = (u.netloc or "").lower()
    path = u.path or ""

    # youtube.com/watch?v=ID
    if host.endswith("youtube.com"):
        if path == "/watch":
            q = urllib.parse.parse_qs(u.query or "")
            v = (q.get("v") or [""])[0]
            if _VIDEO_ID_RE.match(v):
                return v

        # /shorts/ID or /embed/ID
        m = re.match(r"^/(shorts|embed)/([A-Za-z0-9_-]{11})", path)
        if m:
            return m.group(2)

    # youtu.be/ID
    if host == "youtu.be":
        seg = path.lstrip("/").split("/")[0]
        if _VIDEO_ID_RE.match(seg):
            return seg

    raise ValueError("could not extract video id from URL")
