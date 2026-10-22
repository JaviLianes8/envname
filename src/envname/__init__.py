"""Validate and sanitize environment variable names against POSIX, shell and OS rules.

``Rules`` names the three rule sets, so a type checker catches a misspelt one:

>>> from envname import Rules, is_valid_env_name
>>> rules: Rules = "portable"
>>> [is_valid_env_name(name, rules=rules) for name in ("HOME", "home", "1HOME")]
[True, False, False]
"""

from __future__ import annotations

from ._rules import InvalidEnvName, Rules, check_env_name, is_valid_env_name
from ._sanitize import sanitize_env_name

__version__ = "1.0.0"

__all__ = [
    "InvalidEnvName",
    "Rules",
    "check_env_name",
    "is_valid_env_name",
    "sanitize_env_name",
]

# Report the public home of each object, so pickles, tracebacks and help() never
# depend on the private module layout.
for _public in (InvalidEnvName, check_env_name, is_valid_env_name, sanitize_env_name):
    _public.__module__ = __name__
del _public
