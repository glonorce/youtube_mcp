"""youtube_mcp.quota_budgeter

Intent:
    Provide deterministic quota and resource budgeting before executing API calls.

Why (Production-grade guardrails):
    - Prevent quota exhaustion (risk R1).
    - Prevent resource exhaustion (memory/time) for huge channels (risk R4).

Model:
    This is an *estimator* + *enforcer*.
    It does not guarantee exact quota cost but provides safe upper bounds.

SSOT:
    All default limits live here.

Notes:
    - YouTube Data API typical read operations cost ~1 unit.
    - search.list costs ~100 units. (See plan.md / official docs.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


OrderStrategy = Literal["uploads_playlist", "local_sort", "search_api"]


# SSOT default safety limits (tuneable, but must be explicit)
DEFAULT_MAX_VIDEOS: Final[int] = 200
DEFAULT_MAX_PAGES: Final[int] = 10
DEFAULT_VIDEOS_LIST_BATCH: Final[int] = 50  # videos.list supports up to 50 ids per call

# Quota cost constants (approximate, from official docs)
QUOTA_COST_READ: Final[int] = 1
QUOTA_COST_SEARCH: Final[int] = 100


@dataclass(frozen=True, slots=True)
class QuotaBudget:
    """Budget constraints for a single tool execution."""

    max_videos: int = DEFAULT_MAX_VIDEOS
    max_pages: int = DEFAULT_MAX_PAGES
    max_quota_units: int = 1_000  # hard stop per tool call


@dataclass(frozen=True, slots=True)
class QuotaEstimate:
    """Estimated quota for a planned execution."""

    estimated_units: int
    strategy: OrderStrategy
    notes: tuple[str, ...]


class QuotaBudgetExceeded(ValueError):
    """Raised when a plan would exceed budget constraints."""


def estimate_channel_videos_quota(
    *,
    strategy: OrderStrategy,
    requested_max_videos: int,
    budget: QuotaBudget,
    include_video_details: bool,
) -> QuotaEstimate:
    """Estimate and enforce quota budget for listing channel videos.

    Intent:
        Predict the upper bound of quota usage before making calls.

    Assumptions:
        - uploads playlist listing uses playlistItems.list (1 unit per page)
        - videos enrichment uses videos.list (1 unit per batch of up to 50 ids)
        - search_api uses search.list (100 units per page) and is capped by API behavior

    Raises:
        QuotaBudgetExceeded: if the requested plan violates the budget.
    """

    # ---- ADIM 1 — Intent (micro_decision_protocol)
    # Ensure we do not exceed quota / resource budgets.

    if requested_max_videos <= 0:
        raise ValueError("requested_max_videos must be positive")

    max_videos = min(requested_max_videos, budget.max_videos)

    # Compute pages for playlistItems.list (maxResults=50)
    pages = (max_videos + 49) // 50
    pages = min(pages, budget.max_pages)

    notes: list[str] = []
    if requested_max_videos > budget.max_videos:
        notes.append("requested_max_videos truncated to budget.max_videos")

    if pages < (max_videos + 49) // 50:
        notes.append("pages truncated to budget.max_pages")

    if strategy == "uploads_playlist" or strategy == "local_sort":
        units = pages * QUOTA_COST_READ
        if include_video_details:
            batches = (max_videos + (DEFAULT_VIDEOS_LIST_BATCH - 1)) // DEFAULT_VIDEOS_LIST_BATCH
            units += batches * QUOTA_COST_READ

        if units > budget.max_quota_units:
            raise QuotaBudgetExceeded(
                f"Estimated quota {units} exceeds max_quota_units={budget.max_quota_units}"
            )

        return QuotaEstimate(
            estimated_units=units,
            strategy=strategy,
            notes=tuple(notes),
        )

    if strategy == "search_api":
        # Search is expensive and also capped (API note: channelId+type=video max 500 results)
        # We enforce conservative behavior: max 500 videos.
        capped_videos = min(max_videos, 500)
        if capped_videos < max_videos:
            notes.append("search_api is capped to 500 videos by API behavior")
        pages = min((capped_videos + 49) // 50, budget.max_pages)
        units = pages * QUOTA_COST_SEARCH

        if include_video_details:
            batches = (capped_videos + (DEFAULT_VIDEOS_LIST_BATCH - 1)) // DEFAULT_VIDEOS_LIST_BATCH
            units += batches * QUOTA_COST_READ

        if units > budget.max_quota_units:
            raise QuotaBudgetExceeded(
                f"Estimated quota {units} exceeds max_quota_units={budget.max_quota_units}"
            )

        return QuotaEstimate(
            estimated_units=units,
            strategy=strategy,
            notes=tuple(notes),
        )

    raise ValueError(f"Unknown strategy: {strategy}")
