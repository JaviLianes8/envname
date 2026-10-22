"""The command line when the reader of stderr or stdout has gone: the status is kept."""

from __future__ import annotations

import errno
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from envname._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"
ENV = {**os.environ, "PYTHONPATH": str(SRC)}

# The stream whose reader has gone, argv, and the exit status the GUIDE promises.
CASES = [
    ("stderr", ["check", "PATH"], 0),
    ("stderr", ["check", "1A"], 1),
    ("stderr", ["check", *["1A"] * 3000, "PATH"], 1),
    ("stderr", ["sanitize", "--prefix", "1-", "x"], 2),
    ("stderr", ["--bogus"], 2),
    ("stderr", ["bogus"], 2),
    ("stdout", ["--version"], 0),
    ("stdout", ["--help"], 0),
    ("stdout", ["check", "--help"], 0),
    ("stdout", ["sanitize", "db.host"], 141),
]


@pytest.mark.parametrize(("gone", "argv", "status"), CASES)
def test_a_process_whose_reader_has_gone_keeps_its_exit_status(
    gone: str, argv: list[str], status: int
) -> None:
    # The read end is closed before the child starts, so its first write must fail.
    read, write = os.pipe()
    os.close(read)
    on_stderr = gone == "stderr"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "envname", *argv],
            stdout=subprocess.PIPE if on_stderr else write,
            stderr=write if on_stderr else subprocess.PIPE,
            check=False,
            env=ENV,
            timeout=120,
        )
    finally:
        os.close(write)
    # Nothing on the other stream: no usage line on stdout, no "Exception ignored" on stderr.
    other = result.stdout if on_stderr else result.stderr
    assert (result.returncode, other) == (status, b"")


class _GoneReader(io.StringIO):
    def __init__(self, error: OSError) -> None:
        super().__init__()
        self.error = error
        self.writes = 0

    def write(self, text: str) -> int:
        self.writes += 1
        raise self.error


@pytest.mark.parametrize(
    ("platform", "error"),
    [
        (sys.platform, BrokenPipeError(errno.EPIPE, "Broken pipe")),
        # Windows reports a pipe whose reader has gone as EINVAL.
        ("win32", OSError(errno.EINVAL, "Invalid argument")),
    ],
)
def test_check_whose_stderr_reader_has_gone_stops_reporting_and_exits_one(
    platform: str, error: OSError, monkeypatch: pytest.MonkeyPatch
) -> None:
    stream = _GoneReader(error)
    monkeypatch.setattr(sys, "stderr", stream)
    monkeypatch.setattr(sys, "platform", platform)
    assert main(["check", "1A", "2B", "PATH"]) == 1
    assert stream.writes == 1


def test_check_does_not_hide_a_stderr_error_other_than_a_gone_reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stderr", _GoneReader(OSError(errno.ENOSPC, "No space left")))
    with pytest.raises(OSError) as caught:
        main(["check", "1A"])
    assert caught.value.errno == errno.ENOSPC


def test_help_whose_stdout_reader_has_gone_still_exits_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdout", _GoneReader(BrokenPipeError(errno.EPIPE, "Broken pipe")))
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0
