"""Fetch the third-party files listed in tests/upstream/MANIFEST.json.

The files (specifications, the Unicode Character Database, upstream sources) are not
part of the repository. Their tests skip until this script has fetched them; each
download is checked against the size and sha256 in the manifest.

    python scripts/fetch_upstream.py            # fetch and verify
    python scripts/fetch_upstream.py --update   # fetch and record the new size and sha256

Every URL names a fixed revision (a commit, a release or a versioned path), so the
same bytes come back for everyone. An entry with a ``member`` is a release archive: the
archive is checked against ``archive_size`` and ``archive_sha256`` and only that member
is saved.
"""

from __future__ import annotations

import datetime
import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / "tests" / "upstream"


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "envname-tests"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body: bytes = response.read()
    return body


def _member(archive: bytes, member: str) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as tar:
        extracted = tar.extractfile(member)
        if extracted is None:
            raise KeyError(f"{member} is not a regular file")
        return extracted.read()


def _matches(entry: dict[str, object], body: bytes, prefix: str = "") -> bool:
    digest = hashlib.sha256(body).hexdigest()
    return len(body) == entry[prefix + "size"] and digest == entry[prefix + "sha256"]


def _record(entry: dict[str, object], body: bytes, prefix: str = "") -> None:
    entry[prefix + "size"] = len(body)
    entry[prefix + "sha256"] = hashlib.sha256(body).hexdigest()


def main(argv: list[str], folder: Path = FOLDER) -> int:
    update = "--update" in argv
    manifest_path = folder / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failed = 0
    for name, entry in manifest.items():
        archive = body = _download(entry["url"])
        member = entry.get("member")
        if member is not None:
            if not update and not _matches(entry, archive, "archive_"):
                print(f"{name}: the archive differs from the manifest")
                failed += 1
                continue
            body = _member(archive, member)
        if not update and not _matches(entry, body):
            digest = hashlib.sha256(body).hexdigest()
            print(f"{name}: got {len(body)} bytes, sha256 {digest}; manifest differs")
            failed += 1
            continue
        if update:
            if member is not None:
                _record(entry, archive, "archive_")
            _record(entry, body)
            entry["fetched"] = datetime.date.today().isoformat()
        (folder / name).write_bytes(body)
        print(f"{name}: ok")
    if update:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
