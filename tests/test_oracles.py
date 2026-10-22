"""What the README says about other tools, checked against those tools.

python-dotenv and the Compose interpolation pattern are read from their fetched source
(tests/upstream/MANIFEST.json); python-dotenv is also run when it is installed.
"""

from __future__ import annotations

import io
import itertools
import re

import pytest
from conftest import upstream_text

from envname import is_valid_env_name

ASCII = ["a", "Z", "_", "0", "-", ".", "(", ")", "$", "@"]


def _ascii_corpus() -> list[str]:
    return ["".join(chars) for n in (1, 2, 3) for chars in itertools.product(ASCII, repeat=n)]


def _dotenv_key_pattern() -> str:
    source = upstream_text("python-dotenv-parser.py.txt")
    found = re.search(r'^_unquoted_key = make_regex\(r"(.+)"\)$', source, flags=re.MULTILINE)
    assert found, "python-dotenv no longer defines _unquoted_key"
    return found.group(1)


def test_python_dotenv_keys_are_anything_without_equals_hash_or_whitespace() -> None:
    assert _dotenv_key_pattern() == r"([^=\#\s]+)"


def test_python_dotenv_loads_keys_a_shell_cannot_use() -> None:
    dotenv = pytest.importorskip("dotenv")
    pattern = re.compile(_dotenv_key_pattern())
    names = [*_ascii_corpus(), "ProgramFiles(x86)", "my-var", "a#b", "a b", "\u00e9t\u00e9"]
    lines = "".join(f"{name}=v\n" for name in names)
    loaded = dotenv.dotenv_values(stream=io.StringIO(lines))
    for name in names:
        assert (name in loaded) == (pattern.fullmatch(name) is not None), name
    assert "my-var" in loaded and not is_valid_env_name("my-var")
    assert all(is_valid_env_name(name, rules="environ") for name in loaded)


def test_compose_interpolates_shell_names_ignoring_case() -> None:
    source = upstream_text("compose-go-template.go")
    named = re.search(r'substitutionNamed\s*=\s*"(.+)"', source)
    assert named and named.group(1) == "[_a-z][_a-z0-9]*"
    assert '"%s(?i:(?P<%s>%s)|' in source
    # Go folds case for the Kelvin sign and the long s too; for ASCII names the
    # pattern is exactly the shell rule set.
    compose = re.compile(named.group(1), flags=re.IGNORECASE | re.ASCII)
    for name in _ascii_corpus():
        assert (compose.fullmatch(name) is not None) == is_valid_env_name(name), name
