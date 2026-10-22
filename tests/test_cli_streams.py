"""The command line without a stderr (pythonw, `2>&-`): same exit codes, nothing written."""

from __future__ import annotations

import errno
import io
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import find_bash

from envname import __version__
from envname._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"
ENV = {**os.environ, "PYTHONPATH": str(SRC)}

# argv, the exit status the GUIDE promises for it, and all it may print on stdout.
CASES = [
    (["check", "PATH"], 0, ""),
    (["check", "1A", "PATH", "MY-VAR"], 1, ""),
    (["sanitize", "--prefix", "1-", "x"], 2, ""),
    (["check", "--rules", "posix", "A"], 2, ""),
    (["sanitize"], 2, ""),
    (["--version"], 0, f"envname {__version__}\n"),
    (["sanitize", "a.b"], 0, "A_B\n"),
]


def _status(argv: list[str]) -> int:
    try:
        return main(argv)
    except SystemExit as exc:
        assert isinstance(exc.code, int)
        return exc.code


@pytest.mark.parametrize(("argv", "status", "out"), CASES)
def test_without_a_stderr_the_status_is_kept_and_usage_stays_off_stdout(
    argv: list[str],
    status: int,
    out: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stderr", None)
    assert _status(argv) == status
    # argparse falls back to stdout for the usage line, where it would pass for a name.
    assert capsys.readouterr().out == out


@pytest.mark.parametrize(("argv", "status", "out"), CASES)
def test_without_any_standard_stream_every_exit_status_is_kept(
    argv: list[str], status: int, out: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # What pythonw sees: neither stdout nor stderr exists.
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    assert _status(argv) == status


class _FullDisk(io.StringIO):
    def write(self, text: str) -> int:
        raise OSError(errno.ENOSPC, "No space left on device")


def test_a_usage_error_that_cannot_be_written_still_exits_two(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Every supported Python behaves as 3.11+ argparse: the message is lost, not the status.
    monkeypatch.setattr(sys, "stderr", _FullDisk())
    assert _status(["sanitize", "--prefix", "1-", "x"]) == 2


def test_run_as_a_module_without_a_stderr_exits_one_for_an_invalid_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(sys, "argv", ["envname", "check", "1X"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("envname", run_name="__main__")
    assert caught.value.code == 1


@pytest.mark.parametrize(("argv", "status", "out"), CASES)
def test_a_process_started_with_stderr_closed_keeps_its_exit_status(
    argv: list[str], status: int, out: str
) -> None:
    bash = find_bash()
    if bash is None:
        pytest.skip("bash is not installed")
    script = '"$0" -m envname "$@" 2>&-; echo "status $?"'
    result = subprocess.run(
        [bash, "-c", script, sys.executable, *argv],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )
    assert (result.stdout, result.stderr) == (f"{out}status {status}\n", "")


@pytest.mark.parametrize(("argv", "status", "out"), CASES)
def test_pythonw_keeps_every_exit_status(argv: list[str], status: int, out: str) -> None:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.is_file():
        pytest.skip("pythonw is only on Windows")
    # No stdio arguments: a GUI-subsystem child starts with no standard handles at all.
    result = subprocess.run(
        [str(pythonw), "-m", "envname", *argv], check=False, env=ENV, timeout=60
    )
    assert result.returncode == status
