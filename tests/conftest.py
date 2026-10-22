"""Shared helpers: third-party files checked against their manifest."""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def upstream_bytes(name: str) -> bytes:
    """Return a third-party file, checked against its manifest entry.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body


def upstream_text(name: str) -> str:
    """Return a fetched text file as it is."""
    return upstream_bytes(name).decode("utf-8")


def upstream_prose(name: str) -> str:
    """Return a fetched HTML page as plain text: tags removed, whitespace collapsed."""
    text = re.sub(r"<[^>]+>", " ", upstream_text(name))
    return re.sub(r"\s+", " ", html.unescape(text))


def sentence(prose: str, start: str) -> str:
    """Return the sentence of ``prose`` that begins with ``start``, up to its full stop."""
    index = prose.find(start)
    assert index >= 0, start
    end = prose.find(". ", index)
    assert end > index, start
    return prose[index:end]
