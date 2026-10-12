"""The README examples run and print what they say; metadata agrees with the code."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

import envname
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
