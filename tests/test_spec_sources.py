"""The rule sets match the fetched specifications, read from their own text.

The sources are listed in tests/upstream/MANIFEST.json (URL, revision, sha256) and
fetched by scripts/fetch_upstream.py; each test skips while its file is absent.
"""

from __future__ import annotations

import re

import pytest
from conftest import sentence, upstream_prose, upstream_text

from envname import is_valid_env_name

# Every code point up to U+02FF, the line and paragraph separators, a surrogate, a
# full-width letter, the Kelvin sign (which folds to "k") and an astral character.
PROBES = [chr(code) for code in range(0x300)] + ["\u2028", "\u2029", "\ud800", "\uff21"]
PROBES += ["\u212a", "\U0001f600"]


def _portable_character_set() -> dict[str, str]:
    # Rows of the 6.1 table: symbolic name, glyph, <Uxxxx> code, description.
    page = upstream_text("posix-xbd-chap06.html")
    cell = r'<td[^>]*>\s*<p class="tent">(.*?)</p>\s*</td>\s*'
    rows = re.findall(r"<tr[^>]*>\s*" + cell * 4 + r"</tr>", page, flags=re.DOTALL)
    table = {}
    for _symbol, _glyph, code, description in rows:
        found = re.fullmatch(r"&lt;U([0-9A-F]{4})&gt;", code)
        if found:
            table[chr(int(found.group(1), 16))] = description
    assert len(table) > 90, len(table)
    return table


def _classes() -> dict[str, set[str]]:
    table = _portable_character_set()

    def described(start: str) -> set[str]:
        return {char for char, text in table.items() if text.startswith(start)}

    return {
        "upper": described("LATIN CAPITAL LETTER "),
        "lower": described("LATIN SMALL LETTER "),
        "digits": described("DIGIT "),
        "underscore": described("LOW LINE"),
    }


def test_shell_names_are_the_xbd_3_216_definition() -> None:
    prose = upstream_prose("posix-xbd-chap03.html")
    definition = sentence(prose, "3.216 Name In the shell command language")
    assert definition.endswith(
        "a word consisting solely of underscores, digits, and alphabetics from the portable "
        "character set"
    )
    assert sentence(prose, "The first character of a name is not a digit")
    sets = _classes()
    first = sets["upper"] | sets["lower"] | sets["underscore"]
    rest = first | sets["digits"]
    for char in PROBES:
        assert is_valid_env_name(char) == (char in first), repr(char)
        assert is_valid_env_name("A" + char) == (char in rest), repr(char)
        assert is_valid_env_name(char + "A") == (char in first), repr(char)


def test_portable_names_are_the_xbd_8_1_utility_names() -> None:
    prose = upstream_prose("posix-xbd-chap08.html")
    rule = sentence(prose, "Environment variable names used by the utilities")
    assert rule.endswith(
        "consist solely of uppercase letters, digits, and the <underscore> ( '_' ) from the "
        "characters defined in Portable Character Set and do not begin with a digit"
    )
    sets = _classes()
    first = sets["upper"] | sets["underscore"]
    rest = first | sets["digits"]
    for char in PROBES:
        assert is_valid_env_name(char, rules="portable") == (char in first), repr(char)
        assert is_valid_env_name("A" + char, rules="portable") == (char in rest), repr(char)


def test_every_variable_xbd_chapter_8_names_is_portable() -> None:
    page = upstream_text("posix-xbd-chap08.html")
    # TZ is the last variable of 8.3; the terms after it (offset, rule, n) are fields of
    # the TZ format, not variables.
    variables = page[: page.index("<dt><i>TZ</i></dt>") + len("<dt><i>TZ</i></dt>")]
    defined = re.findall(r"<dt><i>([^<]+)</i></dt>", variables)
    # The table of names "frequently exported by widely used command interpreters".
    tabled = re.findall(r'<p class="tent"><i>([^<&]+)</i></p>', page)
    assert {"LANG", "LC_ALL", "PATH", "TZ"} <= set(defined)
    assert len(defined) == 24, defined
    assert {"ARFLAGS", "PS1", "MAILPATH"} <= set(tabled)
    assert len(tabled) == 77, tabled
    for name in defined + tabled:
        assert is_valid_env_name(name, rules="portable"), name
        assert is_valid_env_name(name.lower()), name
        assert not is_valid_env_name(name.lower(), rules="portable"), name


def test_lower_case_names_are_left_to_applications() -> None:
    prose = upstream_prose("posix-xbd-chap08.html")
    assert sentence(prose, "The name space of environment variable names containing lowercase")
    assert sentence(prose, "Uppercase and lowercase letters shall retain their unique identities")
    assert is_valid_env_name("app_home") and not is_valid_env_name("app_home", rules="portable")
    assert is_valid_env_name("Home") and is_valid_env_name("HOME")


@pytest.mark.parametrize(
    ("source", "start", "wording"),
    [
        ("posix-xbd-chap08.html", "These strings have the form", "shall not contain any bytes"),
        ("posix-setenv.html", "The envname argument points to an empty string", "'=' character"),
        ("windows-environment-variables.html", "The name of an environment variable", "(=)"),
    ],
)
def test_environ_rejects_what_the_sources_forbid(source: str, start: str, wording: str) -> None:
    assert wording in sentence(upstream_prose(source), start)
    assert not is_valid_env_name("", rules="environ")
    for name in ["=", "=A", "A=", "A=B", "A==B", "=C:"]:
        assert not is_valid_env_name(name, rules="environ"), name
    for char in PROBES:
        expected = char not in "=\x00"
        assert is_valid_env_name("A" + char, rules="environ") == expected, repr(char)


def test_shell_names_are_the_bash_manual_definition() -> None:
    prose = upstream_prose("bash-manual.html")
    assert sentence(prose, "A word consisting solely of letters, numbers, and underscores") == (
        "A word consisting solely of letters, numbers, and underscores, and beginning with a "
        "letter or underscore"
    )
    assert is_valid_env_name("_") and is_valid_env_name("a1")
    assert not is_valid_env_name("1a")
