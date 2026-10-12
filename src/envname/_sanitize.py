"""Turn arbitrary text into a valid environment variable name."""

from __future__ import annotations

import re
import unicodedata

from ._rules import _require_str, check_env_name

_INVALID_RUN = re.compile(r"[^A-Za-z0-9_]+")
_MARKS = frozenset({"Mn", "Me"})


def _fold_to_ascii(text: str) -> str:
    # NFKD splits an accented letter into the base letter plus a combining mark and
    # maps compatibility forms (ligatures, full-width letters, circled digits) to plain
    # ones; dropping the marks keeps the letter instead of losing it to an underscore.
    decomposed = unicodedata.normalize("NFKD", text)
    # Some marks (the grapheme joiner, variation selectors) have combining class 0, so
    # the general category decides what counts as a mark.
    return "".join(char for char in decomposed if unicodedata.category(char) not in _MARKS)


def sanitize_env_name(s: str, *, upper: bool = True, prefix: str = "") -> str:
    """Turn an arbitrary string into a valid environment variable name.

    Accented and compatibility letters are folded to ASCII, each remaining run of
    characters outside ``[A-Za-z0-9_]`` collapses to one underscore, ``prefix`` (a
    valid shell name, or empty) goes in front, an underscore is added when the result
    would be empty or start with a digit, and the whole name is upper-cased unless
    ``upper`` is False. The result is always a valid ``shell`` name, and a valid
    ``portable`` one when upper-cased.
    """
    text = _require_str(s, "s")
    head = _require_str(prefix, "prefix")
    if head:
        check_env_name(head)
    name = head + _INVALID_RUN.sub("_", _fold_to_ascii(text))
    if not name or name[0].isdigit():
        name = "_" + name
    return name.upper() if upper else name
