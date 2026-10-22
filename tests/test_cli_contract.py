"""The command line's promises on its edges: bounded, secret-safe errors and odd streams."""

from __future__ import annotations

import errno
import io
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import find_bash

from envname._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"
_UNRECOGNIZED = "unrecognized arguments: "


def _last_error_line(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    return captured.err.splitlines()[-1]


def test_an_unknown_rules_value_hides_what_follows_its_equals_sign(
    capsys: pytest.CaptureFixture[str],
) -> None:
    line = _last_error_line(["check", "--rules", "TOKEN=hunter2", "A"], capsys)
    assert "hunter2" not in line
    assert line == (
        "envname check: error: argument --rules: invalid choice: 'TOKEN'... (13 characters) "
        "(choose from 'shell', 'portable', 'environ')"
    )


def test_an_unknown_rules_value_is_quoted_up_to_sixty_characters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    line = _last_error_line(["check", "--rules", "x" * 200, "A"], capsys)
    assert line == (
        f"envname check: error: argument --rules: invalid choice: {'x' * 60!r}... "
        "(200 characters) (choose from 'shell', 'portable', 'environ')"
    )


def _unrecognized(length: int) -> str:
    # An unknown option whose usage message is exactly `length` characters long.
    return "-" + "y" * (length - len(_UNRECOGNIZED) - 1)


def test_a_usage_message_of_three_hundred_characters_is_shown_whole(
    capsys: pytest.CaptureFixture[str],
) -> None:
    argument = _unrecognized(300)
    line = _last_error_line(["sanitize", "a", argument], capsys)
    assert line == f"envname: error: {_UNRECOGNIZED}{argument}"


@pytest.mark.parametrize("length", [301, 2066])
def test_a_longer_usage_message_is_cut_at_three_hundred_and_gives_its_length(
    length: int, capsys: pytest.CaptureFixture[str]
) -> None:
    message = _UNRECOGNIZED + _unrecognized(length)
    line = _last_error_line(["sanitize", "a", _unrecognized(length)], capsys)
    assert line == f"envname: error: {message[:300]}... ({length} characters)"


def test_check_help_shows_the_rule_sets_as_the_guide_does(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["check", "--help"])
    assert caught.value.code == 0
    usage = re.sub(r"\s+", " ", capsys.readouterr().out)
    assert "usage: envname check [-h] [--rules {shell,portable,environ}] NAME [NAME ...]" in usage
    guide = (Path(__file__).resolve().parents[1] / "GUIDE.md").read_text(encoding="utf-8")
    assert "envname check [--rules {shell,portable,environ}] NAME..." in guide


class _FullDisk(io.StringIO):
    def write(self, text: str) -> int:
        raise OSError(errno.ENOSPC, "No space left on device")


def test_a_write_error_other_than_a_gone_reader_is_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdout", _FullDisk())
    with pytest.raises(OSError) as caught:
        main(["sanitize", "a"])
    assert caught.value.errno == errno.ENOSPC


def test_sanitize_without_any_stdout_prints_nothing_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # pythonw, a detached service or `>&-` start Python with sys.stdout set to None.
    monkeypatch.setattr(sys, "stdout", None)
    assert main(["sanitize", "a.b", "c"]) == 0
    assert capsys.readouterr().err == ""


def test_a_process_started_with_stdout_closed_exits_zero_without_a_traceback() -> None:
    bash = find_bash()
    if bash is None:
        pytest.skip("bash is not installed")
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    result = subprocess.run(
        [bash, "-c", '"$0" -m envname sanitize a.b >&-; echo "status $?"', sys.executable],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert (result.stdout, result.stderr) == ("status 0\n", "")
