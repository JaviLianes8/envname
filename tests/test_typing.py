"""The public API is typed: mypy infers results and rejects bad calls."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
from envname import InvalidEnvName, Rules, check_env_name, is_valid_env_name, sanitize_env_name

rules: Rules = "portable"
reveal_type(is_valid_env_name("PATH", rules=rules))
reveal_type(check_env_name("PATH"))
reveal_type(sanitize_env_name("db.host", prefix="APP_"))
reveal_type(InvalidEnvName("1A", "shell", "it starts with a digit", 0).index)
is_valid_env_name("PATH", rules="posix")
check_env_name(b"PATH")
sanitize_env_name("x", True)
bad: Rules = "SHELL"
reveal_type(InvalidEnvName("1A", "shell", "it starts with a digit", 0).rules)
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (5, "bool"),
        (6, "str"),
        (7, "str"),
        (8, "int | None"),
        (13, "Literal['shell'] | Literal['portable'] | Literal['environ']"),
    ],
)
def test_results_are_typed(mypy_output: str, line: int, expected: str) -> None:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", mypy_output)
    assert match, mypy_output
    # Older mypy releases spell builtins with their module prefix and unions as Union.
    revealed = match.group(1).replace("builtins.", "")
    revealed = re.sub(r"Union\[(.+), None\]", r"\1 | None", revealed)
    assert revealed == expected


@pytest.mark.parametrize(
    ("line", "code"),
    [(9, "arg-type"), (10, "arg-type"), (11, "call-arg"), (12, "assignment")],
)
def test_wrong_calls_are_rejected(mypy_output: str, line: int, code: str) -> None:
    assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output
