"""POSIX environment variable name validation and sanitization."""

from __future__ import annotations

import re

_VALID_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_INVALID_RUN = re.compile(r"[^A-Za-z0-9_]+")


def is_valid_env_name(s: str) -> bool:
    """Report whether s is a valid POSIX environment variable name.

    A name must match ``[A-Za-z_][A-Za-z0-9_]*``: it starts with a letter or an
    underscore, contains only letters, digits and underscores, is never empty and
    carries no ``=``. Matching is case-sensitive, as the shell treats names.
    """
    return bool(_VALID_NAME.fullmatch(s))


def sanitize_env_name(s: str, *, upper: bool = True) -> str:
    """Turn an arbitrary string into a valid POSIX environment variable name.

    Each run of characters outside ``[A-Za-z0-9_]`` collapses to a single
    underscore, an underscore is prefixed when the result would start with a digit
    or be empty, and the name is upper-cased unless ``upper`` is False.
    """
    name = _INVALID_RUN.sub("_", s)
    if not name or name[0].isdigit():
        name = "_" + name
    return name.upper() if upper else name
