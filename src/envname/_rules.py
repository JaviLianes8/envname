"""Environment variable name rule sets and the checks behind them."""

from __future__ import annotations

import re
from typing import Literal, cast, get_args

Rules = Literal["shell", "portable", "environ"]
"""The rule sets a name can be checked against.

``shell``: the POSIX shell ``name`` (XBD 3.216), ``[A-Za-z_][A-Za-z0-9_]*``.
``portable``: the names the POSIX utilities use (XBD 8.1), ``[A-Z_][A-Z0-9_]*``.
``environ``: anything the environment itself can hold: not empty, no ``=``, no NUL.
"""

RULES: tuple[str, ...] = get_args(Rules)

_FAST = {
    "shell": re.compile(r"[A-Za-z_][A-Za-z0-9_]*"),
    "portable": re.compile(r"[A-Z_][A-Z0-9_]*"),
    "environ": re.compile(r"[^=\x00]+"),
}
_ALLOWED = {
    "shell": frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"),
    "portable": frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"),
}
_DIGITS = frozenset("0123456789")


class InvalidEnvName(ValueError):
    """Raised by ``check_env_name`` when a name breaks the chosen rules.

    ``index`` is the position of the first offending character, or None when the
    name as a whole is the problem (it is empty).
    """

    def __init__(self, name: str, rules: Rules, reason: str, index: int | None = None) -> None:
        # args must match __init__ so that unpickling can call the class again.
        super().__init__(name, rules, reason, index)
        self.name = name
        self.rules: Rules = rules
        self.reason = reason
        self.index = index

    def __str__(self) -> str:
        where = "" if self.index is None else f" at index {self.index}"
        return f"invalid {self.rules} environment variable name {self.name!r}: {self.reason}{where}"


def _require_str(value: object, what: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{what} must be str, not {type(value).__name__}")
    # An exact str copy: a subclass could override iteration or indexing and make
    # the explanation disagree with the regular expression that judged the name.
    return str.__str__(value)


def _require_rules(rules: object) -> Rules:
    # Compare an exact str, so an object with a permissive __eq__ cannot slip through.
    chosen = str.__str__(rules) if isinstance(rules, str) else None
    if chosen not in _FAST:
        raise ValueError(f"rules must be one of {', '.join(map(repr, RULES))}, not {rules!r}")
    return cast(Rules, chosen)


def _problem(name: str, rules: Rules) -> tuple[str, int | None]:
    if not name:
        return "it is empty", None
    if rules == "environ":
        for index, char in enumerate(name):
            if char == "=":
                return "'=' separates the name from the value", index
            if char == "\x00":
                return "NUL ends the string early", index
    elif name[0] in _DIGITS:
        return "it starts with a digit", 0
    else:
        for index, char in enumerate(name):
            if char not in _ALLOWED[rules]:
                if rules == "portable" and char.isascii() and char.islower():
                    return f"lower-case {char!r} is not portable", index
                return f"{char!r} is not allowed", index
    raise AssertionError("unreachable: the fast pattern rejected a valid name")


def is_valid_env_name(name: str, *, rules: Rules = "shell") -> bool:
    """Report whether ``name`` is a valid environment variable name under ``rules``.

    Raises ``TypeError`` when ``name`` is not a string and ``ValueError`` for an
    unknown rule set.
    """
    text = _require_str(name, "name")
    return _FAST[_require_rules(rules)].fullmatch(text) is not None


def check_env_name(name: str, *, rules: Rules = "shell") -> str:
    """Return ``name`` as a plain ``str`` if it is valid under ``rules``.

    Raises ``InvalidEnvName`` (a ``ValueError``) naming the reason and the index of
    the first offending character otherwise.
    """
    text = _require_str(name, "name")
    chosen = _require_rules(rules)
    if _FAST[chosen].fullmatch(text) is None:
        reason, index = _problem(text, chosen)
        raise InvalidEnvName(text, chosen, reason, index)
    return text
