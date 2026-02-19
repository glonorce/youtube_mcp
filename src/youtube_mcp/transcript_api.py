"""youtube_mcp.transcript_api

Intent:
    Transcript extraction adapter.

Design constraints:
    - The package must remain importable even when optional extractor
      dependencies are not installed.
    - Fail-fast when invoked without dependencies.

Notes:
    - Uses `yt_ts_extract` for robust transcript extraction.
"""

from __future__ import annotations

from typing import Any, Callable

from .logger import get_logger

logger = get_logger(__name__)


# Optional dependency (do not raise at import-time).
try:
    from yt_ts_extract import (  # type: ignore
        YouTubeTranscriptExtractor,
        get_available_languages,
        get_transcript,
        get_transcript_text,
    )
except ModuleNotFoundError:
    YouTubeTranscriptExtractor = None  # type: ignore[assignment]
    get_available_languages = None  # type: ignore[assignment]
    get_transcript = None  # type: ignore[assignment]
    get_transcript_text = None  # type: ignore[assignment]


def get_video_transcript(video_id: str, languages: list[str] | None = None) -> str | None:
    """Fetch the transcript for a YouTube video with fallback logic.

    Args:
        video_id: The ID of the YouTube video.
        languages: Preferred language codes (default: ["en"]).

    Returns:
        Transcript text, or None if not found.

    Raises:
        RuntimeError: if optional extractor dependency is not installed.
    """

    if YouTubeTranscriptExtractor is None:
        raise RuntimeError(
            "yt_ts_extract is not installed; cannot fetch transcripts. "
            "Install project dependencies to enable this capability."
        )

    preferred = languages or ["en"]

    try:
        logger.info("Fetching transcript", extra={"video_id": video_id})

        extractor = YouTubeTranscriptExtractor(
            timeout=30,
            max_retries=3,
            backoff_factor=0.75,
            min_delay=2.0,
        )

        # Get available languages (best-effort)
        try:
            assert get_available_languages is not None
            available_langs = get_available_languages(video_id)
            logger.info(
                "Available languages",
                extra={"video_id": video_id, "codes": [lang.get("code") for lang in available_langs]},
            )
        except Exception as e:
            logger.info("Could not get available languages", extra={"video_id": video_id, "error": str(e)})
            available_langs = []

        transcript: Any = None
        for lang in preferred:
            try:
                logger.info("Trying transcript language", extra={"video_id": video_id, "lang": lang})
                transcript = extractor.get_transcript(video_id, language=lang)
                if transcript:
                    break
            except Exception as e:
                logger.info(
                    "Failed transcript language",
                    extra={"video_id": video_id, "lang": lang, "error": str(e)},
                )

        # Fallback: generic get_transcript
        if not transcript:
            try:
                assert get_transcript is not None
                transcript = get_transcript(video_id)
            except Exception as e:
                logger.info("Fallback get_transcript failed", extra={"video_id": video_id, "error": str(e)})

        # Fallback: text
        if not transcript:
            try:
                assert get_transcript_text is not None
                text = get_transcript_text(video_id)
                if isinstance(text, str) and text.strip():
                    return text
            except Exception as e:
                logger.info("Fallback get_transcript_text failed", extra={"video_id": video_id, "error": str(e)})

        # Normalize segments
        if isinstance(transcript, list):
            texts: list[str] = []
            for seg in transcript:
                if isinstance(seg, dict) and isinstance(seg.get("text"), str):
                    texts.append(seg["text"])
            joined = " ".join(texts).strip()
            return joined or None

        if isinstance(transcript, str):
            return transcript.strip() or None

        return None

    except Exception as e:
        # Maintain backward-compatible behavior: return a user-readable string.
        return f"Could not retrieve transcript: {e}"
