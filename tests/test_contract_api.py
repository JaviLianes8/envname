"""The complete promise of every public name: signature, result and failure types."""

from __future__ import annotations

import inspect
import pickle
import typing

import pytest

import envname
from envname import InvalidEnvName, Rules, check_env_name, is_valid_env_name, sanitize_env_name

SIGNATURES = {
    "is_valid_env_name": "(name: 'str', *, rules: 'Rules' = 'shell') -> 'bool'",
    "check_env_name": "(name: 'str', *, rules: 'Rules' = 'shell') -> 'str'",
    "sanitize_env_name": "(text: 'str', *, upper: 'bool' = True, prefix: 'str' = '') -> 'str'",
}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_function_signatures_are_pinned(name: str) -> None:
    assert str(inspect.signature(getattr(envname, name))) == SIGNATURES[name]


def test_error_constructor_is_pinned() -> None:
    assert str(inspect.signature(InvalidEnvName)) == (
        "(name: 'str', rules: 'Rules', reason: 'str', index: 'int | None' = None) -> 'None'"
    )


def test_rules_are_exactly_three_literals_in_order() -> None:
    assert typing.get_origin(Rules) is typing.Literal
    assert typing.get_args(Rules) == ("shell", "portable", "environ")


def test_public_objects_live_in_the_package() -> None:
    for obj in (InvalidEnvName, check_env_name, is_valid_env_name, sanitize_env_name):
        assert obj.__module__ == "envname", obj
    dumped = pickle.dumps(InvalidEnvName("1A", "shell", "it starts with a digit", 0))
    assert b"envname" in dumped and b"_rules" not in dumped


def test_every_public_name_is_documented_with_an_example() -> None:
    for name in ("InvalidEnvName", "check_env_name", "is_valid_env_name", "sanitize_env_name"):
        doc = inspect.getdoc(getattr(envname, name)) or ""
        assert ">>> " in doc, name
    # A Literal alias has no docstring of its own; the package docstring shows it.
    assert ">>> rules: Rules = " in (envname.__doc__ or "")


def test_error_is_a_value_error_with_its_fields() -> None:
    error = InvalidEnvName("A-B", "shell", "'-' is not allowed", 1)
    assert isinstance(error, ValueError)
    assert error.args == ("A-B", "shell", "'-' is not allowed", 1)
    assert (error.name, error.rules, error.reason, error.index) == (
        "A-B",
        "shell",
        "'-' is not allowed",
        1,
    )
    assert InvalidEnvName("", "environ", "it is empty").index is None


def test_messages_quote_at_most_sixty_characters() -> None:
    name = "A" * 60
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name(name + "-")
    assert caught.value.name == name + "-"
    assert str(caught.value) == (
        f"invalid shell environment variable name {name!r}... (61 characters): "
        "'-' is not allowed at index 60"
    )
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name(name.lower(), rules="portable")
    assert str(caught.value) == (
        f"invalid portable environment variable name {name.lower()!r}: "
        "lower-case 'a' is not portable at index 0"
    )


def test_a_megabyte_name_gives_a_short_message() -> None:
    huge = "x" * 1_000_000 + "="
    for rules in ("shell", "environ"):
        with pytest.raises(InvalidEnvName) as caught:
            check_env_name(huge, rules=rules)
        assert len(str(caught.value)) < 200
        assert "(1000001 characters)" in str(caught.value)
        assert caught.value.index == 1_000_000


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: is_valid_env_name(b"PATH"),  # type: ignore[arg-type]
            "name must be str, not bytes",
        ),
        (
            lambda: check_env_name(None),  # type: ignore[arg-type]
            "name must be str, not NoneType",
        ),
        (
            lambda: sanitize_env_name(1),  # type: ignore[arg-type]
            "text must be str, not int",
        ),
        (
            lambda: sanitize_env_name("x", prefix=b"A"),  # type: ignore[arg-type]
            "prefix must be str, not bytes",
        ),
    ],
)
def test_wrong_types_raise_type_error_with_a_fixed_message(call: object, message: str) -> None:
    with pytest.raises(TypeError) as caught:
        call()  # type: ignore[operator]
    assert str(caught.value) == message


@pytest.mark.parametrize(
    ("rules", "shown"),
    [
        ("posix", "'posix'"),
        ("SHELL", "'SHELL'"),
        (None, "NoneType"),
        (["shell"], "list"),
        ("z" * 100, repr("z" * 60) + "... (100 characters)"),
    ],
)
def test_unknown_rules_raise_value_error_naming_them_safely(rules: object, shown: str) -> None:
    for function in (is_valid_env_name, check_env_name):
        with pytest.raises(ValueError) as caught:
            function("PATH", rules=rules)  # type: ignore[arg-type]
        assert type(caught.value) is ValueError
        assert str(caught.value) == (
            f"rules must be one of 'shell', 'portable', 'environ', not {shown}"
        )


def test_an_object_whose_repr_fails_is_still_reported() -> None:
    class Hostile:
        def __repr__(self) -> str:
            raise RuntimeError("no repr")

    with pytest.raises(ValueError, match=r"not Hostile$"):
        is_valid_env_name("PATH", rules=Hostile())  # type: ignore[arg-type]


def test_check_returns_an_exact_str_equal_to_the_name() -> None:
    class Name(str):
        pass

    result = check_env_name(Name("PATH"))
    assert type(result) is str and result == "PATH"
    assert is_valid_env_name(Name("PATH")) is True
    assert is_valid_env_name("1") is False
