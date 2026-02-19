"""youtube_mcp.video_comments

Intent:
    Provide a small, testable facade for retrieving YouTube video comments.

Implementation:
    Uses YouTube Data API v3 `commentThreads.list`.

Notes:
    - Public comments only.
    - Comments may be disabled (403 with reason=commentsDisabled).
    - Pagination supported via `pageToken`.
    - `maxResults` supports up to 100 for commentThreads.list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .quota_budgeter import QUOTA_COST_READ, QuotaBudget, QuotaEstimate
from .youtube_client_protocol import IYouTubeClient


CommentOrder = Literal["time", "relevance"]
TextFormat = Literal["plainText", "html"]


@dataclass(frozen=True, slots=True)
class VideoCommentThreadsPage:
    items: tuple[dict[str, Any], ...]
    next_page_token: str | None
    quota_estimate: QuotaEstimate


def list_video_comment_threads_page(
    *,
    client: IYouTubeClient,
    video_id: str,
    page_token: str | None,
    max_threads: int,
    order: CommentOrder,
    text_format: TextFormat,
    include_replies: bool,
    budget: QuotaBudget,
) -> VideoCommentThreadsPage:
    if not video_id or not video_id.strip():
        raise ValueError("video_id is required")

    if max_threads <= 0:
        raise ValueError("max_threads must be positive")

    # commentThreads.list allows 1..100
    if max_threads > 100:
        max_threads = 100

    # Quota: 1 unit per page (official docs)
    if QUOTA_COST_READ > budget.max_quota_units:
        raise ValueError("Quota budget too low")

    part = "snippet,replies" if include_replies else "snippet"

    params: dict[str, str] = {
        "videoId": video_id,
        "maxResults": str(max_threads),
        "order": order,
        "textFormat": text_format,
    }

    if page_token:
        params["pageToken"] = page_token

    resp = client.comment_threads_list(part=part, params=params)

    items = resp.get("items")
    out_items: list[dict[str, Any]] = []
    if isinstance(items, list):
        out_items = [it for it in items if isinstance(it, dict)]

    next_token = resp.get("nextPageToken")
    next_out = next_token if isinstance(next_token, str) and next_token else None

    est = QuotaEstimate(estimated_units=QUOTA_COST_READ, strategy="uploads_playlist", notes=())
    return VideoCommentThreadsPage(items=tuple(out_items), next_page_token=next_out, quota_estimate=est)
