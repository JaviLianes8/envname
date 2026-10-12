"""check_env_name returns valid names and explains invalid ones."""

from __future__ import annotations

import copy
import pickle

import pytest

from envname import InvalidEnvName, check_env_name


def test_returns_the_valid_name_unchanged() -> None:
    assert check_env_name("PATH") == "PATH"
    assert check_env_name("a b", rules="environ") == "a b"


@pytest.mark.parametrize(
    ("name", "rules", "reason", "index"),
    [
        ("", "shell", "it is empty", None),
        ("", "environ", "it is empty", None),
        ("1PATH", "shell", "it starts with a digit", 0),
        ("MY-VAR", "shell", "'-' is not allowed", 2),
        ("ab\u00e9", "shell", "'\u00e9' is not allowed", 2),
        ("PATH\n", "shell", "'\\n' is not allowed", 4),
        ("HOMe", "portable", "lower-case 'e' is not portable", 3),
        ("A\u0130", "portable", "'\u0130' is not allowed", 1),
        ("9a", "portable", "it starts with a digit", 0),
        ("KEY=VALUE", "environ", "'=' separates the name from the value", 3),
        ("=C:", "environ", "'=' separates the name from the value", 0),
        ("A\x00B=", "environ", "NUL ends the string early", 1),
    ],
)
def test_reports_reason_and_first_offending_index(
    name: str, rules: str, reason: str, index: int | None
) -> None:
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name(name, rules=rules)  # type: ignore[arg-type]
    error = caught.value
    assert (error.name, error.rules, error.reason, error.index) == (name, rules, reason, index)


def test_is_a_value_error() -> None:
    with pytest.raises(ValueError):
        check_env_name("1A")


def test_message_names_the_rules_the_name_and_the_position() -> None:
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name("MY-VAR")
    assert str(caught.value) == (
        "invalid shell environment variable name 'MY-VAR': '-' is not allowed at index 2"
    )


def test_message_without_position_for_an_empty_name() -> None:
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name("", rules="portable")
    assert str(caught.value) == "invalid portable environment variable name '': it is empty"


def test_survives_pickle_and_copy() -> None:
    error = InvalidEnvName("1A", "shell", "it starts with a digit", 0)
    for clone in (pickle.loads(pickle.dumps(error)), copy.copy(error), copy.deepcopy(error)):
        assert type(clone) is InvalidEnvName
        assert (clone.name, clone.rules, clone.reason, clone.index) == (
            "1A",
            "shell",
            error.reason,
            0,
        )
        assert str(clone) == str(error)


def test_non_string_raises_type_error() -> None:
    with pytest.raises(TypeError, match="name must be str, not bytes"):
        check_env_name(b"PATH")  # type: ignore[arg-type]


def test_unknown_rules_raise_before_checking() -> None:
    with pytest.raises(ValueError, match="rules must be one of"):
        check_env_name("PATH", rules="posix")  # type: ignore[arg-type]
