"""The README examples run and print what they say; metadata agrees with the code."""

from __future__ import annotations

import doctest
import re
import shlex
import string
import subprocess
import sys
from pathlib import Path

import pytest

import envname
from envname import is_valid_env_name
from envname._cli import main

ROOT = Path(__file__).resolve().parents[1]

TRANSCRIPT = [
    "True",
    "False",
    "False",
    "False",
    "False",
    "True",
    "invalid shell environment variable name 'MY-VAR': '-' is not allowed at index 2",
    "2",
    "DATABASE_URL",
    "MY_VAR_",
    "_1ST_VALUE",
    "CREME_BRULEE",
    "APP_DB_HOST",
    "host_name",
    "['ProgramFiles(x86)', 'my-var']",
    "True",
]


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _blocks(language: str) -> list[str]:
    return re.findall(rf"```{language}\n(.*?)```", _readme(), flags=re.DOTALL)


def test_every_python_example_prints_the_transcript(capsys: pytest.CaptureFixture[str]) -> None:
    blocks = _blocks("python")
    assert len(blocks) == 4
    for block in blocks:
        exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
    assert capsys.readouterr().out.splitlines() == TRANSCRIPT


def test_every_printed_comment_is_real_output() -> None:
    comments = [
        line.split("  # ", 1)[1]
        for block in _blocks("python")
        for line in block.splitlines()
        if line.lstrip().startswith("print(") and "  # " in line
    ]
    assert comments == TRANSCRIPT


def test_every_console_example_prints_what_it_shows(capsys: pytest.CaptureFixture[str]) -> None:
    (block,) = _blocks("console")
    commands = 0
    expected: list[str] = []
    for line in [*block.splitlines(), "$"]:
        if not line.startswith("$"):
            expected.append(line)
            continue
        captured = capsys.readouterr()
        assert (captured.out + captured.err).splitlines() == expected
        expected = []
        if line.startswith("$ envname "):
            commands += 1
            main(shlex.split(line)[2:])
    assert commands == 3


def test_every_public_name_appears_in_the_readme() -> None:
    for name in envname.__all__:
        assert name in _readme(), name


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == envname.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{envname.__version__}]" in text


def test_the_rules_table_lists_every_rule_set() -> None:
    from envname._rules import RULES

    rows = re.findall(r'^\| `"(\w+)"`', _readme(), flags=re.MULTILINE)
    assert rows == list(RULES)


def test_every_guide_example_runs() -> None:
    text = (ROOT / "GUIDE.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```pycon\n(.*?)```", text, flags=re.DOTALL)
    assert len(blocks) == 5
    parser = doctest.DocTestParser()
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    # The blocks read as one session: later blocks use names imported earlier.
    session: dict[str, object] = {}
    for number, block in enumerate(blocks):
        test = parser.get_doctest(block, session, f"GUIDE.md block {number}", "GUIDE.md", 0)
        assert test.examples, number
        runner.run(test, clear_globs=False)
        session.update(test.globs)
    results = runner.summarize(verbose=False)
    assert results.failed == 0 and results.attempted == 15


def test_the_why_section_states_facts() -> None:
    # Each claim the README makes about another tool, run here.
    assert "\u00e9t\u00e9".isidentifier() and "\ufb01le".isidentifier()
    assert not is_valid_env_name("\u00e9t\u00e9") and not is_valid_env_name("\ufb01le")
    assert string.Template.idpattern == r"(?a:[_a-z][_a-z0-9]*)"
    # Python 3.14 leaves Template.flags as None and applies IGNORECASE by default.
    assert string.Template.pattern.flags & re.IGNORECASE
    assert "`(?a:[_a-z][_a-z0-9]*)` with `re.IGNORECASE`" in _readme()
    accepted = subprocess.run(
        [sys.executable, "-I", "-c", "import os; os.putenv('my-var', 'v')"], check=False
    )
    assert accepted.returncode == 0 and not is_valid_env_name("my-var")
    assert is_valid_env_name("ProgramFiles(x86)", rules="environ")


WINDOWS_LIMITS = """
import ctypes, os
def refused(name, value):
    try:
        os.putenv(name, value)
    except ValueError:
        return True
    return False
assert not refused("A", "v" * 32765) and refused("A", "v" * 32766)
assert not refused("B" * 32766, "") and refused("B" * 32767, "")
kernel = ctypes.WinDLL("kernel32")
kernel.SetEnvironmentVariableW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
kernel.GetEnvironmentVariableW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
name, buffer = "Q" * 40000, ctypes.create_unicode_buffer(8)
assert kernel.SetEnvironmentVariableW(name, "v")
assert kernel.GetEnvironmentVariableW(name, buffer, 8) == 1 and buffer.value == "v"
"""


@pytest.mark.skipif(sys.platform != "win32", reason="the claim is about Windows")
def test_the_windows_length_limits_are_as_stated() -> None:
    assert "can hold 32,766 characters" in _readme()
    # A child process, so the oversized variable never lands in this one.
    result = subprocess.run([sys.executable, "-I", "-c", WINDOWS_LIMITS], check=False)
    assert result.returncode == 0
