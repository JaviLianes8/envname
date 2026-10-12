"""sanitize_env_name always yields a valid name and keeps as much of the input as it can."""

from __future__ import annotations

import random

import pytest

from envname import InvalidEnvName, check_env_name, is_valid_env_name, sanitize_env_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("my  var!!name", "MY_VAR_NAME"),
        ("1st-value", "_1ST_VALUE"),
        ("host.name", "HOST_NAME"),
        ("", "_"),
        ("@#$", "_"),
        ("Cr\u00e8me br\u00fbl\u00e9e", "CREME_BRULEE"),
        ("e\u0301t\u00e9", "ETE"),
        ("\ufb01le", "FILE"),
        ("\uff21\uff22", "AB"),
        ("\u2460x", "_1X"),
        ("stra\u00dfe", "STRA_E"),
        ("\u00f8l", "_L"),
        ("PATH", "PATH"),
        ("a\u034fb", "AB"),
        ("x\u20ddy", "XY"),
    ],
)
def test_sanitizes(raw: str, expected: str) -> None:
    assert sanitize_env_name(raw) == expected


def test_keeps_case_when_upper_is_false() -> None:
    assert sanitize_env_name("My-Var", upper=False) == "My_Var"
    assert sanitize_env_name("Cr\u00e8me", upper=False) == "Creme"


def test_prefix_goes_in_front_and_is_upper_cased() -> None:
    assert sanitize_env_name("db.host", prefix="app_") == "APP_DB_HOST"
    assert sanitize_env_name("db.host", prefix="App_", upper=False) == "App_db_host"


def test_prefix_removes_the_need_for_a_leading_underscore() -> None:
    assert sanitize_env_name("1st", prefix="APP_") == "APP_1ST"
    assert sanitize_env_name("", prefix="APP") == "APP"


@pytest.mark.parametrize("prefix", ["1APP_", "APP-", "app.", " "])
def test_invalid_prefix_is_rejected(prefix: str) -> None:
    with pytest.raises(InvalidEnvName):
        sanitize_env_name("x", prefix=prefix)


@pytest.mark.parametrize(("arg", "value"), [("s", None), ("s", b"x"), ("prefix", None)])
def test_non_string_input_raises_type_error(arg: str, value: object) -> None:
    kwargs: dict[str, object] = {"s": "x", arg: value}
    with pytest.raises(TypeError, match=f"{arg} must be str"):
        sanitize_env_name(**kwargs)  # type: ignore[arg-type]


def test_output_is_ascii_even_for_letters_with_wide_upper_case() -> None:
    # "\u0149".upper() is two characters and "\u0131".upper() is "I": upper-casing
    # must happen after the text is ASCII, or the result could stop being a name.
    for raw in ["\u0149", "\u0131x", "\u00df", "\u1fb3"]:
        result = sanitize_env_name(raw)
        assert result.isascii(), result
        assert is_valid_env_name(result, rules="portable"), result


def _random_text(rng: random.Random) -> str:
    pools = [
        "abcXYZ019_",
        "-=. \t\n\x00/$#",
        "\u00e9\u00df\u0130\u0131\u00f8\ufb01\uff21\u2460\u0301\u1fb3\U0001f600",
    ]
    return "".join(rng.choice(rng.choice(pools)) for _ in range(rng.randrange(0, 12)))


def test_output_is_always_valid_and_stable() -> None:
    rng = random.Random(20261012)
    for _ in range(5000):
        raw = _random_text(rng)
        upper = sanitize_env_name(raw)
        kept = sanitize_env_name(raw, upper=False)
        assert check_env_name(upper, rules="portable") == upper
        assert check_env_name(kept, rules="shell") == kept
        assert kept.upper() == upper
        assert sanitize_env_name(upper) == upper, raw


def test_valid_names_pass_through_unchanged() -> None:
    for name in ["PATH", "_X", "LC_ALL", "A1_B2"]:
        assert sanitize_env_name(name) == name
        assert sanitize_env_name(name.lower(), upper=False) == name.lower()
