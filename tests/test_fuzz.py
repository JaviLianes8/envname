"""Seeded random and hostile input: an independent model of each rule set agrees.

The model below is written from the grammars, character by character, without regular
expressions; the library must agree with it on every generated name.
"""

from __future__ import annotations

import random
import string
import time

import pytest

from envname import InvalidEnvName, check_env_name, is_valid_env_name, sanitize_env_name

SEEDS = [20261022, 7, 99991]
POOLS = [
    string.ascii_letters + string.digits + "_",
    "-=. \t\n\r\x00\x0b/$#()[]{}'\"\\",
    "\u00e9\u00df\u0130\u0131\u00f8\ufb01\uff21\uff10\u0663\u212a\u017f\u0301\u2028\ud800",
    "\U0001f600\U00010400\u3000\u200d\ufeff",
]
LETTERS = set(string.ascii_letters)
UPPER = set(string.ascii_uppercase)
DIGITS = set(string.digits)
# 60 quoted characters of at most 10 escaped characters each, plus the fixed wording.
LONGEST_MESSAGE = 800


def _model(name: str, rules: str) -> int | bool | None:
    """Return True when valid, else the offending index (None for an empty name)."""
    if not name:
        return None
    if rules == "environ":
        for index, char in enumerate(name):
            if char in "=\x00":
                return index
        return True
    first = (UPPER if rules == "portable" else LETTERS) | {"_"}
    if name[0] in DIGITS:
        return 0
    for index, char in enumerate(name):
        if char not in first | DIGITS:
            return index
    return True


def _names(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    names = []
    for _ in range(count):
        size = rng.choice([0, 1, 2, 3, 5, 8, 20, 70])
        names.append("".join(rng.choice(rng.choice(POOLS)) for _ in range(size)))
    return names


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("rules", ["shell", "portable", "environ"])
def test_every_name_agrees_with_the_model(seed: int, rules: str) -> None:
    for name in _names(seed, 4000):
        verdict = _model(name, rules)
        assert is_valid_env_name(name, rules=rules) == (verdict is True), repr(name)  # type: ignore[arg-type]
        if verdict is True:
            assert check_env_name(name, rules=rules) == name  # type: ignore[arg-type]
            continue
        with pytest.raises(InvalidEnvName) as caught:
            check_env_name(name, rules=rules)  # type: ignore[arg-type]
        error = caught.value
        assert (error.name, error.rules, error.index) == (name, rules, verdict), repr(name)
        assert len(str(error)) <= LONGEST_MESSAGE


@pytest.mark.parametrize("seed", SEEDS)
def test_sanitized_names_are_valid_and_stable(seed: int) -> None:
    for text in _names(seed, 4000):
        upper = sanitize_env_name(text)
        kept = sanitize_env_name(text, upper=False)
        assert _model(upper, "portable") is True, repr(text)
        assert _model(kept, "shell") is True, repr(text)
        assert kept.upper() == upper
        assert sanitize_env_name(upper) == upper
        prefixed = sanitize_env_name(text, prefix="APP_")
        core = prefixed.removeprefix("APP_")
        # The prefix replaces the underscore that guards an empty or digit-first name.
        assert prefixed.startswith("APP_") and upper in (core, "_" + core), repr(text)


SHAPES = {
    "valid": lambda n: "A" * n,
    "bad at the end": lambda n: "A" * n + "-",
    "digit first": lambda n: "1" + "A" * n,
    "non-ASCII": lambda n: "\u00e9" * n,
    "equals": lambda n: "=" * n,
    "NUL at the end": lambda n: "a" * n + "\x00",
    "marks": lambda n: "e\u0301" * n,
    "runs": lambda n: "a-" * n,
}


def _elapsed(text: str) -> float:
    start = time.perf_counter()
    for rules in ("shell", "portable", "environ"):
        try:
            check_env_name(text, rules=rules)
        except InvalidEnvName as error:
            assert len(str(error)) <= LONGEST_MESSAGE
    sanitize_env_name(text)
    return time.perf_counter() - start


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_huge_input_is_linear_and_messages_stay_short(shape: str) -> None:
    small = min(_elapsed(SHAPES[shape](20_000)) for _ in range(3))
    large = min(_elapsed(SHAPES[shape](200_000)) for _ in range(3))
    # Ten times the input: allow forty times the time, never a quadratic hundred.
    assert large < small * 40 + 0.05, (shape, small, large)
