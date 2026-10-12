"""Validate and sanitize environment variable names against POSIX, shell and OS rules."""

from __future__ import annotations

from ._rules import InvalidEnvName, Rules, check_env_name, is_valid_env_name
from ._sanitize import sanitize_env_name

__version__ = "0.2.0"

__all__ = [
    "InvalidEnvName",
    "Rules",
    "check_env_name",
    "is_valid_env_name",
    "sanitize_env_name",
]
