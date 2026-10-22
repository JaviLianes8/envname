"""Folding to ASCII matches the Unicode Character Database itself.

``sanitize_env_name`` uses Python's ``unicodedata``. This test rebuilds the expected
result for single characters from the fetched UnicodeData.txt of the same Unicode
version (decomposition mappings and general categories), independently of
``unicodedata``, and compares.
"""

from __future__ import annotations

import re
import unicodedata

import pytest
from conftest import UPSTREAM, upstream_text

from envname import sanitize_env_name

HANGUL = range(0xAC00, 0xD7A4)
Database = tuple[dict[int, str], dict[int, list[int]], list[tuple[int, int, str]]]


def _database() -> Database:
    name = f"UnicodeData-{unicodedata.unidata_version}.txt"
    if not (UPSTREAM / name).is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    categories: dict[int, str] = {}
    mappings: dict[int, list[int]] = {}
    ranges: list[tuple[int, int, str]] = []
    first = 0
    for line in upstream_text(name).splitlines():
        fields = line.split(";")
        code, label, category, mapping = int(fields[0], 16), fields[1], fields[2], fields[5]
        if label.endswith(", First>"):
            first = code
            continue
        if label.endswith(", Last>"):
            ranges.append((first, code, category))
            continue
        categories[code] = category
        if mapping:
            # Compatibility mappings start with a <tag>; NFKD applies both kinds.
            mappings[code] = [int(part, 16) for part in re.sub(r"<\w+>", "", mapping).split()]
    return categories, mappings, ranges


def _category(code: int, categories: dict[int, str], ranges: list[tuple[int, int, str]]) -> str:
    if code in categories:
        return categories[code]
    for low, high, category in ranges:
        if low <= code <= high:
            return category
    return "Cn"


def _decompose(code: int, mappings: dict[int, list[int]]) -> list[int]:
    if code in HANGUL:
        return [code]  # decomposes to jamo, which are letters but not ASCII either way
    if code not in mappings:
        return [code]
    return [part for child in mappings[code] for part in _decompose(child, mappings)]


def _expected(code: int, database: Database) -> str:
    categories, mappings, ranges = database
    kept = [
        chr(part)
        for part in _decompose(code, mappings)
        if _category(part, categories, ranges) not in ("Mn", "Me")
    ]
    name = re.sub(r"[^A-Za-z0-9_]+", "_", "".join(kept))
    return "_" + name if not name or name[0].isdigit() else name


def test_single_characters_fold_as_the_database_says() -> None:
    database = _database()
    categories, _, ranges = database
    codes = set(categories) | {low for low, _, _ in ranges} | {high for _, high, _ in ranges}
    codes |= set(range(0, 0x110000, 251))  # unassigned and range interiors as well
    folded = 0
    for code in sorted(codes):
        expected = _expected(code, database)
        assert sanitize_env_name(chr(code), upper=False) == expected, hex(code)
        assert sanitize_env_name(chr(code)) == expected.upper(), hex(code)
        folded += expected.strip("_") != ""
    assert len(codes) > 30000, len(codes)
    # Well over a thousand characters keep a letter or digit, not just the 62 ASCII ones.
    assert folded > 1500, folded


def test_marks_after_a_letter_are_dropped() -> None:
    categories, _, _ = _database()
    marks = [code for code, category in categories.items() if category in ("Mn", "Me")]
    assert len(marks) > 1000
    for code in marks:
        assert sanitize_env_name("a" + chr(code) + "b", upper=False) == "ab", hex(code)
