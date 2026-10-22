"""The command line checks and sanitizes, with exit codes scripts can rely on."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from envname._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def test_check_exits_zero_when_every_name_is_valid(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "PATH", "_x1"]) == 0
    assert capsys.readouterr() == ("", "")


def test_check_reports_every_invalid_name_and_exits_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["check", "OK", "1A", "MY-VAR"]) == 1
    assert capsys.readouterr().err.splitlines() == [
        "envname: invalid shell environment variable name '1A': it starts with a digit at index 0",
        "envname: invalid shell environment variable name 'MY-VAR': '-' is not allowed at index 2",
    ]


def test_check_honours_rules(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "--rules", "environ", "my-var"]) == 0
    assert main(["check", "--rules", "portable", "path"]) == 1
    assert "lower-case 'p' is not portable" in capsys.readouterr().err


def test_check_rejects_unknown_rules(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["check", "--rules", "posix", "PATH"])
    assert caught.value.code == 2
    assert "invalid choice: 'posix'" in capsys.readouterr().err


def test_check_escapes_what_the_console_cannot_show(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252")
    monkeypatch.setattr(sys, "stderr", stream)
    assert main(["check", "A\u01c4"]) == 1
    stream.flush()
    assert rb"'A\u01c4'" in raw.getvalue()


def test_sanitize_prints_one_name_per_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sanitize", "db.host", "1st", "--prefix", "app_"]) == 0
    assert capsys.readouterr().out.splitlines() == ["APP_DB_HOST", "APP_1ST"]


def test_sanitize_keep_case(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sanitize", "--keep-case", "Cr\u00e8me br\u00fbl\u00e9e"]) == 0
    assert capsys.readouterr().out == "Creme_brulee\n"


def test_sanitize_rejects_an_invalid_prefix(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["sanitize", "--prefix", "1-", "x"])
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "envname sanitize: error: --prefix: invalid shell environment variable name '1-'" in (
        captured.err
    )


def test_a_command_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main([])
    assert caught.value.code == 2


def test_runs_as_a_module() -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    result = subprocess.run(
        [sys.executable, "-m", "envname", "check", "PATH", "--", "-x"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 1
    assert "'-x': '-' is not allowed at index 0" in result.stderr


def test_version_prints_the_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    from envname import __version__

    with pytest.raises(SystemExit) as caught:
        main(["--version"])
    assert caught.value.code == 0
    assert capsys.readouterr().out == f"envname {__version__}\n"


@pytest.mark.parametrize(("command", "argument"), [("check", "NAME"), ("sanitize", "TEXT")])
def test_a_missing_argument_is_a_usage_error(
    command: str, argument: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as caught:
        main([command])
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"error: the following arguments are required: {argument}" in captured.err


def test_keep_case_keeps_the_prefix_as_given(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sanitize", "--keep-case", "--prefix", "app_", "db.host"]) == 0
    assert capsys.readouterr().out == "app_db_host\n"


@pytest.mark.parametrize(
    "argv",
    [
        ["check", "--rules", "x" * 30_000, "A"],
        ["x" * 30_000],
        ["check", "--" + "x" * 30_000 + "=1", "A"],
    ],
)
def test_usage_errors_stay_short(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 2
    assert len(capsys.readouterr().err) < 1000


def test_unknown_rules_name_the_choices(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["check", "--rules", "posix", "A"])
    assert capsys.readouterr().err.splitlines()[-1] == (
        "envname check: error: argument --rules: invalid choice: 'posix' "
        "(choose from 'shell', 'portable', 'environ')"
    )


class _ClosedPipe(io.StringIO):
    def write(self, text: str) -> int:
        raise BrokenPipeError(32, "Broken pipe")


def test_sanitize_stops_quietly_when_the_reader_has_gone(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", _ClosedPipe())
    assert main(["sanitize", "a", "b"]) == 141
    assert capsys.readouterr().err == ""


def test_a_closed_pipe_ends_the_process_without_a_traceback() -> None:
    # The read end is closed before the child starts, so its first write must fail.
    read, write = os.pipe()
    os.close(read)
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "envname", "sanitize", "db.host", "max conn"],
            stdout=write,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=env,
        )
    finally:
        os.close(write)
    assert (result.returncode, result.stderr) == (141, "")
