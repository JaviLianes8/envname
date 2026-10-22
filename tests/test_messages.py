"""Error messages and reprs stay short and never show what follows an "=" in a name."""

from __future__ import annotations

import pickle

import pytest

from envname import InvalidEnvName, check_env_name, is_valid_env_name, sanitize_env_name
from envname._cli import main

SECRET = "sk_live_Z9Z9Z9"


@pytest.mark.parametrize(
    ("name", "rules", "message"),
    [
        (
            f"API_KEY={SECRET}",
            "environ",
            "invalid environ environment variable name 'API_KEY'... (22 characters): "
            "'=' separates the name from the value at index 7",
        ),
        (
            f"API_KEY={SECRET}",
            "shell",
            "invalid shell environment variable name 'API_KEY'... (22 characters): "
            "'=' is not allowed at index 7",
        ),
        (
            f"my-key={SECRET}",
            "shell",
            "invalid shell environment variable name 'my-key'... (21 characters): "
            "'-' is not allowed at index 2",
        ),
        (
            f"=C:{SECRET}",
            "environ",
            "invalid environ environment variable name ''... (17 characters): "
            "'=' separates the name from the value at index 0",
        ),
    ],
)
def test_message_stops_before_the_first_equals_sign(name: str, rules: str, message: str) -> None:
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name(name, rules=rules)  # type: ignore[arg-type]
    assert str(caught.value) == message
    assert caught.value.name == name
    assert SECRET not in repr(caught.value)


def test_long_name_before_the_equals_sign_is_still_cut_at_sixty() -> None:
    name = "A" * 70 + "=" + SECRET
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name(name, rules="environ")
    assert str(caught.value) == (
        f"invalid environ environment variable name {'A' * 60!r}... (85 characters): "
        "'=' separates the name from the value at index 70"
    )


def test_an_invalid_prefix_does_not_show_its_value() -> None:
    with pytest.raises(InvalidEnvName) as caught:
        sanitize_env_name("x", prefix="TOKEN=abc")
    assert "abc" not in str(caught.value) and "abc" not in repr(caught.value)
    with pytest.raises(ValueError) as unknown:
        is_valid_env_name("PATH", rules="TOKEN=abc")  # type: ignore[arg-type]
    assert "abc" not in str(unknown.value)


def test_command_line_does_not_print_the_value(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "DB_PASSWORD=hunter2"]) == 1
    assert "hunter2" not in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(["sanitize", "--prefix", "TOKEN=hunter2", "x"])
    assert "hunter2" not in capsys.readouterr().err


def test_repr_is_as_short_as_the_message() -> None:
    with pytest.raises(InvalidEnvName) as caught:
        check_env_name("A" * 10_000_000 + "-")
    error = caught.value
    assert len(repr(error)) < 200
    assert repr(error) == (
        f"InvalidEnvName({'A' * 60!r}... (10000001 characters), 'shell', "
        "\"'-' is not allowed\", 10000000)"
    )
    assert repr(InvalidEnvName("1A", "shell", "it starts with a digit", 0)) == (
        "InvalidEnvName('1A', 'shell', 'it starts with a digit', 0)"
    )
    # The whole name still travels with the error, through pickling too.
    again = pickle.loads(pickle.dumps(error))
    assert again.name == error.name and repr(again) == repr(error)
