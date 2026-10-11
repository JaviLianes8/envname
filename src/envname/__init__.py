"""Validate and sanitize POSIX environment variable names."""

from __future__ import annotations

from ._names import is_valid_env_name, sanitize_env_name

__version__ = "0.1.0"

__all__ = ["is_valid_env_name", "sanitize_env_name"]
