"""scripts/fetch_upstream.py saves exactly the pinned bytes, and every source is pinned.

The downloads are injected: these tests never touch the network.
"""

from __future__ import annotations

import datetime
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "fetch_upstream", ROOT / "scripts" / "fetch_upstream.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tar(member: str, body: bytes) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo(member)
        info.size = len(body)
        tar.addfile(info, io.BytesIO(body))
    return buffer.getvalue()


def _pin(body: bytes, prefix: str = "") -> dict[str, object]:
    return {prefix + "size": len(body), prefix + "sha256": hashlib.sha256(body).hexdigest()}


_script_module = _script()


@pytest.fixture
def served(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    pages: dict[str, bytes] = {}
    monkeypatch.setattr(_script_module, "_download", pages.__getitem__)
    return pages


def _manifest(folder: Path, entries: dict[str, dict[str, object]]) -> None:
    (folder / "MANIFEST.json").write_text(json.dumps(entries), encoding="utf-8")


def test_saves_files_and_archive_members_that_match(
    served: dict[str, bytes], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    archive = _tar("pkg-1.0/doc/manual.html", b"<p>manual</p>")
    served.update({"https://a/page": b"page", "https://a/pkg.tar.gz": archive})
    _manifest(
        tmp_path,
        {
            "page.txt": {"url": "https://a/page", **_pin(b"page")},
            "manual.html": {
                "url": "https://a/pkg.tar.gz",
                "member": "pkg-1.0/doc/manual.html",
                **_pin(archive, "archive_"),
                **_pin(b"<p>manual</p>"),
            },
        },
    )
    assert _script_module.main([], tmp_path) == 0
    assert (tmp_path / "page.txt").read_bytes() == b"page"
    assert (tmp_path / "manual.html").read_bytes() == b"<p>manual</p>"
    assert capsys.readouterr().out.splitlines() == ["page.txt: ok", "manual.html: ok"]


def test_refuses_bytes_that_differ_from_the_manifest(
    served: dict[str, bytes], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    archive = _tar("pkg/doc.html", b"new")
    served.update({"https://a/page": b"changed", "https://a/pkg.tar.gz": archive})
    _manifest(
        tmp_path,
        {
            "page.txt": {"url": "https://a/page", **_pin(b"page")},
            "doc.html": {
                "url": "https://a/pkg.tar.gz",
                "member": "pkg/doc.html",
                **_pin(b"old archive", "archive_"),
                **_pin(b"new"),
            },
        },
    )
    assert _script_module.main([], tmp_path) == 1
    assert not (tmp_path / "page.txt").exists() and not (tmp_path / "doc.html").exists()
    out = capsys.readouterr().out
    assert "page.txt: got 7 bytes" in out and "doc.html: the archive differs" in out


def test_every_source_names_a_fixed_revision() -> None:
    manifest = json.loads((ROOT / "tests" / "upstream" / "MANIFEST.json").read_text("utf-8"))
    for name, entry in manifest.items():
        revision = entry["revision"]
        assert "as served" not in revision, name
        if revision.startswith("commit "):
            assert revision.removeprefix("commit ") in entry["url"], name
        for field in ("url", "licence", "fetched", "size", "sha256"):
            assert entry[field], (name, field)
        assert ("member" in entry) == ("archive_sha256" in entry), name


def test_refuses_bytes_of_the_pinned_size_with_another_sha256(
    served: dict[str, bytes], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    served["https://a/page"] = b"pagf"
    _manifest(tmp_path, {"page.txt": {"url": "https://a/page", **_pin(b"page")}})
    assert _script_module.main([], tmp_path) == 1
    assert not (tmp_path / "page.txt").exists()
    assert "page.txt: got 4 bytes" in capsys.readouterr().out


def test_update_saves_the_files_and_records_their_new_pins(
    served: dict[str, bytes], tmp_path: Path
) -> None:
    archive = _tar("pkg/doc.html", b"new manual")
    served.update({"https://a/page": b"new page bytes", "https://a/pkg.tar.gz": archive})
    stale = {"size": 1, "sha256": "0", "fetched": "2000-01-01"}
    _manifest(
        tmp_path,
        {
            "page.txt": {"url": "https://a/page", **stale},
            "doc.html": {
                "url": "https://a/pkg.tar.gz",
                "member": "pkg/doc.html",
                "archive_size": 1,
                "archive_sha256": "0",
                **stale,
            },
        },
    )
    before = datetime.date.today().isoformat()
    assert _script_module.main(["--update"], tmp_path) == 0
    after = datetime.date.today().isoformat()
    assert (tmp_path / "page.txt").read_bytes() == b"new page bytes"
    assert (tmp_path / "doc.html").read_bytes() == b"new manual"
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest.values():
        assert entry.pop("fetched") in (before, after)
    assert manifest == {
        "page.txt": {"url": "https://a/page", **_pin(b"new page bytes")},
        "doc.html": {
            "url": "https://a/pkg.tar.gz",
            "member": "pkg/doc.html",
            **_pin(archive, "archive_"),
            **_pin(b"new manual"),
        },
    }
