"""Each rule set accepts and rejects what its source says.

The vectors are written by hand from the grammars quoted in IMPROVEMENTS-round.md;
none of them is copied from an upstream test file.
"""

from __future__ import annotations

import pytest

from envname import is_valid_env_name

SHELL_OK = ["PATH", "path", "Path", "_", "__", "_my_var2", "A1", "a_b_c"]
SHELL_BAD = ["", "1PATH", "9", "MY-VAR", "my var", "KEY=VALUE", "a.b", "\u00e9", "PATH\n", "A\x00"]
PORTABLE_OK = ["PATH", "_", "HOME_2", "_X", "LC_ALL"]
PORTABLE_BAD = ["", "path", "Path", "HOMe", "1A", "A-B", "\u0130", "\uff21", "A\n"]
ENVIRON_OK = ["PATH", "1st", "my-var", "a b", " ", "\u00e9", "\u01c4", "x.y", "\n", "\u2028"]
ENVIRON_BAD = ["", "=", "A=B", "FOO=", "=FOO", "A\x00B", "\x00"]


@pytest.mark.parametrize("name", SHELL_OK)
def test_shell_accepts(name: str) -> None:
    assert is_valid_env_name(name)
    assert is_valid_env_name(name, rules="shell")


@pytest.mark.parametrize("name", SHELL_BAD)
def test_shell_rejects(name: str) -> None:
    assert not is_valid_env_name(name)


@pytest.mark.parametrize("name", PORTABLE_OK)
def test_portable_accepts(name: str) -> None:
    assert is_valid_env_name(name, rules="portable")


@pytest.mark.parametrize("name", PORTABLE_BAD)
def test_portable_rejects(name: str) -> None:
    assert not is_valid_env_name(name, rules="portable")


@pytest.mark.parametrize("name", ENVIRON_OK)
def test_environ_accepts(name: str) -> None:
    assert is_valid_env_name(name, rules="environ")


def test_environ_has_no_length_limit_of_its_own() -> None:
    # Windows caps name=value at 32,767 characters together; a name alone cannot know.
    assert is_valid_env_name("a" * 40000, rules="environ")


@pytest.mark.parametrize("name", ENVIRON_BAD)
def test_environ_rejects(name: str) -> None:
    assert not is_valid_env_name(name, rules="environ")


def test_rules_nest_portable_inside_shell_inside_environ() -> None:
    for name in SHELL_OK + SHELL_BAD + PORTABLE_OK + PORTABLE_BAD + ENVIRON_OK + ENVIRON_BAD:
        if is_valid_env_name(name, rules="portable"):
            assert is_valid_env_name(name, rules="shell"), name
        if is_valid_env_name(name, rules="shell"):
            assert is_valid_env_name(name, rules="environ"), name


@pytest.mark.parametrize("value", [None, b"PATH", 1, ["PATH"]])
def test_non_string_names_raise_type_error(value: object) -> None:
    with pytest.raises(TypeError, match="name must be str"):
        is_valid_env_name(value)  # type: ignore[arg-type]


def test_str_subclasses_are_accepted() -> None:
    class Name(str):
        pass

    assert is_valid_env_name(Name("PATH"))


@pytest.mark.parametrize("rules", ["posix", "SHELL", "", None])
def test_unknown_rules_raise_value_error(rules: object) -> None:
    with pytest.raises(ValueError, match="rules must be one of 'shell', 'portable', 'environ'"):
        is_valid_env_name("PATH", rules=rules)  # type: ignore[arg-type]
