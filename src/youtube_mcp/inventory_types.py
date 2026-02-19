"""youtube_mcp.inventory_types

Intent:
    Shared types for inventory/listing domain modules.

Why:
    Keep domain logic modules small (<100 lines) while preserving strict typing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .quota_budgeter import QuotaEstimate


PartsLevel = Literal["basic", "full"]


@dataclass(frozen=True, slots=True)
class ChannelVideosPage:
    items: tuple[dict[str, Any], ...]
    next_page_token: str | None
    quota_estimate: QuotaEstimate
    truncated: bool
    applied_max_videos: int


class ChannelInventoryError(RuntimeError):
    """Raised for channel inventory failures."""
