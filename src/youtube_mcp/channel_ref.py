"""youtube_mcp.channel_ref

Intent:
    Normalize and classify user-provided channel identifiers into a strict, typed
    internal representation (ChannelRef) that downstream resolvers can handle
    deterministically.

Why this exists:
    - We must support multiple user input forms (handle, channel URL, user URL,
      raw channelId, etc.).
    - We must *not* "guess" ambiguous identifiers in strict mode.

Non-goals (by design):
    - This module does not call external APIs.
    - This module does not resolve custom URLs (/c/...) to channel IDs.

This module is intentionally stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal
from urllib.parse import urlparse


ChannelRefKind = Literal["handle", "channel_id", "username", "custom_url", "query"]


# SSOT: Allowed hostnames for parsing YouTube URLs. (This is *not* an HTTP allowlist.)
_YOUTUBE_HOSTS: Final[frozenset[str]] = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    }
)

# SSOT: Recognized path prefixes
_PATH_AT_HANDLE: Final[str] = "/@"
_PATH_CHANNEL: Final[str] = "/channel/"
_PATH_USER: Final[str] = "/user/"
_PATH_CUSTOM: Final[str] = "/c/"

# SSOT: ChannelId format guardrail (best-effort). Typical channel IDs start with "UC".
# We keep this intentionally permissive to avoid false negatives.
_MIN_CHANNEL_ID_LEN: Final[int] = 16


class ChannelRefParseError(ValueError):
    """Raised when a channel reference cannot be parsed deterministically."""


@dataclass(frozen=True, slots=True)
class ChannelRef:
    """Normalized channel reference.

    Attributes:
        kind:
            The classified kind of identifier.
        value:
            Canonical value for that kind:
              - handle: without leading '@'
              - channel_id: channelId (e.g., UCxxxx)
              - username: legacy username segment
              - custom_url: value after /c/
              - query: a free-form string that needs best-effort resolution
        raw:
            Original user input (trimmed).
    """

    kind: ChannelRefKind
    value: str
    raw: str


def parse_channel_ref(user_input: str) -> ChannelRef:
    """Parse a user-supplied channel reference into a ChannelRef.

    Supported inputs:
        - "@handle" (preferred)
        - "https://www.youtube.com/@handle"
        - "https://www.youtube.com/channel/UC..."
        - "https://www.youtube.com/user/SomeUsername"
        - "UC..." (raw channelId)
        - "youtube.com/..." (scheme-less URLs)
        - "/c/<custom>" and "youtube.com/c/<custom>" -> kind=custom_url
        - Any other non-empty string -> kind=query

    Raises:
        ChannelRefParseError: if the input is empty/invalid.

    Security posture:
        This function does not fetch URLs; it only parses strings.
    """

    # ---- ADIM 1 — Intent (micro_decision_protocol)
    # We classify the input without network calls, enabling strict downstream behavior.

    raw = _normalize_raw(user_input)

    # Fast-path: explicit handle.
    if raw.startswith("@"):
        handle = raw[1:].strip()
        _require_non_empty(handle, "Handle cannot be empty")
        _reject_separators(handle, "Handle")
        return ChannelRef(kind="handle", value=handle, raw=raw)

    # Fast-path: looks like a raw channelId.
    if _looks_like_channel_id(raw):
        return ChannelRef(kind="channel_id", value=raw, raw=raw)

    # URL parsing (scheme optional).
    parsed = _try_parse_youtube_url(raw)
    if parsed is not None:
        return parsed

    # Everything else: treat as query (ambiguous by default).
    return ChannelRef(kind="query", value=raw, raw=raw)


def _normalize_raw(user_input: str) -> str:
    if user_input is None:  # type: ignore[redundant-expr]
        raise ChannelRefParseError("Channel reference is required")

    raw = user_input.strip()
    _require_non_empty(raw, "Channel reference cannot be empty")
    return raw


def _require_non_empty(value: str, message: str) -> None:
    if not value:
        raise ChannelRefParseError(message)


def _reject_separators(value: str, label: str) -> None:
    # Prevent accidental URL-like values being treated as a handle/username.
    # This is a "fail-fast" validation.
    if any(sep in value for sep in ("/", "?", "#")):
        raise ChannelRefParseError(f"{label} contains invalid URL separator characters")


def _looks_like_channel_id(value: str) -> bool:
    # YouTube channel IDs typically look like: UCxxxxxxxxxxxxxxxxxxxxxx
    # We avoid strict regex to prevent false negatives.
    return value.startswith("UC") and len(value) >= _MIN_CHANNEL_ID_LEN and " " not in value


def _try_parse_youtube_url(raw: str) -> ChannelRef | None:
    # Allow scheme-less URLs by prepending https://
    candidate = raw
    if candidate.startswith("youtube.com/") or candidate.startswith("www.youtube.com/") or candidate.startswith("m.youtube.com/"):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)

    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None

    host = (parsed.netloc or "").lower()
    if not host or host not in _YOUTUBE_HOSTS:
        return None

    path = parsed.path or ""

    if path.startswith(_PATH_AT_HANDLE):
        handle = path[len(_PATH_AT_HANDLE) :].strip("/")
        _require_non_empty(handle, "Handle cannot be empty")
        _reject_separators(handle, "Handle")
        return ChannelRef(kind="handle", value=handle, raw=raw)

    if path.startswith(_PATH_CHANNEL):
        channel_id = path[len(_PATH_CHANNEL) :].strip("/")
        _require_non_empty(channel_id, "Channel ID cannot be empty")
        _reject_separators(channel_id, "Channel ID")
        return ChannelRef(kind="channel_id", value=channel_id, raw=raw)

    if path.startswith(_PATH_USER):
        username = path[len(_PATH_USER) :].strip("/")
        _require_non_empty(username, "Username cannot be empty")
        _reject_separators(username, "Username")
        return ChannelRef(kind="username", value=username, raw=raw)

    if path.startswith(_PATH_CUSTOM):
        custom = path[len(_PATH_CUSTOM) :].strip("/")
        _require_non_empty(custom, "Custom URL segment cannot be empty")
        _reject_separators(custom, "Custom URL segment")
        return ChannelRef(kind="custom_url", value=custom, raw=raw)

    # Unknown YouTube path. Keep it ambiguous.
    return ChannelRef(kind="query", value=raw, raw=raw)
