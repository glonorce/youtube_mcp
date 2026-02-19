"""youtube_mcp.redaction

Intent:
    Centralized redaction utilities to prevent sensitive data from appearing in
    logs, exceptions, or tool outputs.

Threat model:
    - API keys can leak via URL query strings or naive dict logging.

This module is SSOT for redaction.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


REDACTED = "[REDACTED]"


def redact_url(url: str) -> str:
    """Redact sensitive query params (e.g., key=) in a URL string."""

    try:
        parts = urlsplit(url)
        if not parts.query:
            return url

        q = []
        for k, v in parse_qsl(parts.query, keep_blank_values=True):
            if k.lower() in {"key", "api_key", "apikey", "token", "access_token"}:
                q.append((k, REDACTED))
            else:
                q.append((k, v))

        new_query = urlencode(q, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
    except Exception:
        return "[UNPARSABLE_URL]"


def redact_mapping(data: Any) -> Any:
    """Recursively redact sensitive keys in dict-like objects.

    This is best-effort and intended for logging only.
    """

    if isinstance(data, dict):
        out: dict[Any, Any] = {}
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in {"key", "api_key", "apikey", "token", "access_token"}:
                out[k] = REDACTED
            else:
                out[k] = redact_mapping(v)
        return out

    if isinstance(data, list):
        return [redact_mapping(x) for x in data]

    if isinstance(data, tuple):
        return tuple(redact_mapping(x) for x in data)

    return data
