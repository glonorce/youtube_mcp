"""youtube_mcp.channel_resolver

Intent:
    Resolve a `ChannelRef` to a concrete YouTube `channelId` and related metadata
    using YouTube Data API v3.

Key requirements:
    - Strict by default: never guess ambiguous inputs.
    - Best-effort mode: may provide candidate channels for user selection.
    - Uses Dependency Inversion: depends on IYouTubeClient protocol.

Non-goals:
    - Fetching full channel video inventory (handled by inventory services).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from .channel_ref import ChannelRef, parse_channel_ref
from .youtube_client_protocol import IYouTubeClient
from .youtube_errors import (
    YouTubeApiBadRequestError,
    YouTubeApiError,
    YouTubeApiMisconfigurationError,
)


ResolutionMode = Literal["strict", "best_effort"]


@dataclass(frozen=True, slots=True)
class ChannelCandidate:
    channel_id: str
    title: str | None
    handle: str | None


@dataclass(frozen=True, slots=True)
class ResolvedChannel:
    channel_id: str
    title: str | None
    handle: str | None
    uploads_playlist_id: str | None
    warnings: tuple[str, ...]
    candidates: tuple[ChannelCandidate, ...] = ()


class ChannelResolutionError(ValueError):
    """Raised when a channel cannot be resolved deterministically."""


def resolve_channel(
    *,
    client: IYouTubeClient,
    channel_ref: str,
    mode: ResolutionMode = "strict",
    include_uploads_playlist: bool = True,
) -> ResolvedChannel:
    """Resolve channel reference string to a ResolvedChannel.

    Args:
        client: IYouTubeClient implementation.
        channel_ref: user input.
        mode: strict or best_effort.
        include_uploads_playlist: whether to request contentDetails.

    Returns:
        ResolvedChannel.

    Raises:
        ChannelResolutionError: for strict mode ambiguous/unresolvable inputs.
        YouTubeApiError: for API failures.
    """

    # ---- ADIM 1 — Intent (micro_decision_protocol)
    # Convert user input into a channelId safely and deterministically.

    ref = parse_channel_ref(channel_ref)

    if ref.kind == "custom_url":
        # Custom URLs (/c/...) cannot be deterministically resolved via channels.list.
        # In strict mode, do not guess.
        if mode == "strict":
            raise ChannelResolutionError(
                "Custom channel URLs (/c/...) cannot be resolved deterministically. "
                "Provide @handle or /channel/<id> or /user/<username>."
            )

        # best effort: treat as query
        ref = ChannelRef(kind="query", value=ref.value, raw=ref.raw)

    if ref.kind == "query":
        if mode == "strict":
            raise ChannelResolutionError(
                "Ambiguous channel reference. Provide @handle, channel URL (/channel/UC...), or /user/<username>."
            )

        return _resolve_best_effort_query(client=client, query=ref.value, include_uploads_playlist=include_uploads_playlist)

    if ref.kind == "handle":
        return _resolve_channels_list(
            client=client,
            filter_params={"forHandle": f"@{ref.value}"},
            include_uploads_playlist=include_uploads_playlist,
        )

    if ref.kind == "channel_id":
        return _resolve_channels_list(
            client=client,
            filter_params={"id": ref.value},
            include_uploads_playlist=include_uploads_playlist,
        )

    if ref.kind == "username":
        return _resolve_channels_list(
            client=client,
            filter_params={"forUsername": ref.value},
            include_uploads_playlist=include_uploads_playlist,
        )

    raise ChannelResolutionError(f"Unsupported channel ref kind: {ref.kind}")


def _resolve_channels_list(
    *,
    client: IYouTubeClient,
    filter_params: Mapping[str, str],
    include_uploads_playlist: bool,
) -> ResolvedChannel:
    part_items: list[str] = ["snippet", "id"]
    if include_uploads_playlist:
        part_items.append("contentDetails")

    part = ",".join(part_items)

    data = client.channels_list(part=part, params=dict(filter_params))
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ChannelResolutionError("Channel not found")

    if len(items) > 1:
        # channels.list should return at most 1 for id/forHandle/forUsername.
        raise ChannelResolutionError("Multiple channels matched unexpectedly")

    item = items[0]
    channel_id = _get_str(item, "id")
    snippet = item.get("snippet") if isinstance(item, dict) else None
    title = _get_str(snippet, "title") if isinstance(snippet, dict) else None
    handle = _get_str(snippet, "customUrl") if isinstance(snippet, dict) else None

    uploads_playlist_id: str | None = None
    warnings: list[str] = []

    if include_uploads_playlist:
        uploads_playlist_id = _extract_uploads_playlist_id(item)
        if uploads_playlist_id is None:
            warnings.append("uploadsPlaylistId not available")

    return ResolvedChannel(
        channel_id=channel_id,
        title=title,
        handle=handle,
        uploads_playlist_id=uploads_playlist_id,
        warnings=tuple(warnings),
    )


def _resolve_best_effort_query(
    *,
    client: IYouTubeClient,
    query: str,
    include_uploads_playlist: bool,
) -> ResolvedChannel:
    # Best-effort uses search.list (expensive; should be opt-in at tool layer).
    # Here we only produce candidates; we do NOT auto-select.
    if not query.strip():
        raise ChannelResolutionError("Query cannot be empty")

    data = client.search_list(part="snippet", params={"q": query, "type": "channel", "maxResults": "5"})
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ChannelResolutionError("No channel candidates found")

    candidates: list[ChannelCandidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        id_block = item.get("id")
        if not isinstance(id_block, dict):
            continue
        channel_id = id_block.get("channelId")
        if not isinstance(channel_id, str) or not channel_id:
            continue
        snippet = item.get("snippet")
        title = _get_str(snippet, "title") if isinstance(snippet, dict) else None
        handle = _get_str(snippet, "channelTitle") if isinstance(snippet, dict) else None
        candidates.append(ChannelCandidate(channel_id=channel_id, title=title, handle=handle))

    # Return unresolved with candidates; tool layer can request user selection.
    return ResolvedChannel(
        channel_id="",
        title=None,
        handle=None,
        uploads_playlist_id=None,
        warnings=("best_effort_candidates_only",),
        candidates=tuple(candidates),
    )


def _extract_uploads_playlist_id(item: Any) -> str | None:
    # Navigate: contentDetails.relatedPlaylists.uploads
    if not isinstance(item, dict):
        return None
    content = item.get("contentDetails")
    if not isinstance(content, dict):
        return None
    related = content.get("relatedPlaylists")
    if not isinstance(related, dict):
        return None
    uploads = related.get("uploads")
    return uploads if isinstance(uploads, str) and uploads else None


def _get_str(obj: Any, key: str) -> str | None:
    if not isinstance(obj, dict):
        return None
    v = obj.get(key)
    return v if isinstance(v, str) and v else None
