"""Unit tests for quota_budgeter.

Intent:
    Prove quota estimation and enforcement is deterministic and safe.
"""

import pytest

from src.youtube_mcp.quota_budgeter import (
    QuotaBudget,
    QuotaBudgetExceeded,
    estimate_channel_videos_quota,
)


def test_estimate_uploads_playlist_basic_quota() -> None:
    budget = QuotaBudget(max_videos=200, max_pages=10, max_quota_units=1000)
    est = estimate_channel_videos_quota(
        strategy="uploads_playlist",
        requested_max_videos=120,
        budget=budget,
        include_video_details=True,
    )
    # pages=3, batches=3 => 6 units
    assert est.estimated_units == 6


def test_estimate_truncates_requested_max_videos() -> None:
    budget = QuotaBudget(max_videos=50, max_pages=10, max_quota_units=1000)
    est = estimate_channel_videos_quota(
        strategy="uploads_playlist",
        requested_max_videos=1000,
        budget=budget,
        include_video_details=False,
    )
    assert est.estimated_units == 1  # 50 videos => 1 page
    assert "truncated" in " ".join(est.notes)


def test_budget_exceeded_raises() -> None:
    budget = QuotaBudget(max_videos=200, max_pages=10, max_quota_units=2)
    with pytest.raises(QuotaBudgetExceeded):
        estimate_channel_videos_quota(
            strategy="uploads_playlist",
            requested_max_videos=200,
            budget=budget,
            include_video_details=True,
        )


def test_search_api_is_capped_to_500() -> None:
    budget = QuotaBudget(max_videos=10_000, max_pages=100, max_quota_units=10_000)
    est = estimate_channel_videos_quota(
        strategy="search_api",
        requested_max_videos=10_000,
        budget=budget,
        include_video_details=False,
    )
    # capped videos=500 => pages=10 => 10*100 = 1000 units
    assert est.estimated_units == 1000
    assert any("capped" in n for n in est.notes)
