"""Centralized logger - provides consistent logging across all modules.

Security hardening:
    - Use redaction utilities for dict logging and URLs.
    - Avoid accidental API key leakage via naive logging.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .redaction import redact_mapping, redact_url

# Create logs directory if it doesn't exist
# Go up to project root: src/youtube_mcp/logger.py -> src/youtube_mcp -> src -> project_root
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "youtube_mcp.log"

FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s"
)

DEBUG_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s"
)

ROOT_LOGGER_NAME = "youtube_mcp"
root_logger = logging.getLogger(ROOT_LOGGER_NAME)
root_logger.setLevel(logging.INFO)

if not root_logger.handlers:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(FORMATTER)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(FORMATTER)
    console_handler.setLevel(logging.ERROR)
    root_logger.addHandler(console_handler)


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger instance for a module."""

    return logging.getLogger(module_name)


def set_log_level(level: int) -> None:
    """Set root log level."""

    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(level)
            handler.setFormatter(DEBUG_FORMATTER if level == logging.DEBUG else FORMATTER)


def log_dict(logger_instance: logging.Logger, level: int, message: str, data: Dict[str, Any]) -> None:
    """Log a dictionary safely (with redaction)."""

    safe = redact_mapping(data)
    logger_instance.log(level, f"{message}: {safe}")


def log_url(logger_instance: logging.Logger, level: int, message: str, url: str) -> None:
    """Log a URL safely (with query redaction)."""

    logger_instance.log(level, f"{message}: {redact_url(url)}")


def log_exception(logger_instance: logging.Logger, message: str, exc_info: Optional[bool] = True) -> None:
    """Log an exception with traceback."""

    logger_instance.exception(message, exc_info=exc_info)
