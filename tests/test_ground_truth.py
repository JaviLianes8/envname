"""The rule sets agree with a real shell and with the real operating system.

The corpus is generated here; the verdicts come from bash and from the OS call that
stores environment variables, each run in a child process so the test process keeps
its own environment.
"""

from __future__ import annotations

import itertools
import json
import os
import shutil
import subprocess
import sys

import pytest

from envname import is_valid_env_name

ALPHABET = ["a", "Z", "_", "0", "9", "-", ".", "=", " ", "\u00e9", "\n"]


def _corpus() -> list[str]:
    names = ["", "PATH", "path", "_", "A=B", "=C:", "FOO=", "1A", "\u01c4", "a" * 300]
    for length in (1, 2, 3):
        names += ["".join(chars) for chars in itertools.product(ALPHABET, repeat=length)]
    return names


def _bash() -> str | None:
    found = shutil.which("bash")
    # On Windows "bash" may be the WSL launcher in System32, which is not a shell here.
    if found is None or "system32" in found.lower():
        return None
    return found


def _bash_literal(name: str) -> str:
    # ANSI-C quoting spells every byte, so spaces, quotes and newlines reach bash intact
    # whatever the platform does to command lines.
    return "$'" + "".join(f"\\x{byte:02x}" for byte in name.encode()) + "'"


def test_shell_rules_match_bash() -> None:
    bash = _bash()
    if bash is None:
        pytest.skip("bash is not installed")
    names = _corpus()
    # One shell for the whole corpus: outside POSIX mode a failed special builtin does
    # not end the shell, and bash checks identifiers the same way in both modes.
    script = "".join(
        f"if unset -v -- {_bash_literal(name)} 2>/dev/null; then echo 1; else echo 0; fi\n"
        for name in names
    )
    result = subprocess.run(
        [bash, "-s"],
        input=script.encode(),
        capture_output=True,
        env={**os.environ, "LC_ALL": "C"},
        check=True,
    )
    verdicts = result.stdout.decode().split()
    for name, verdict in zip(names, verdicts, strict=True):
        assert is_valid_env_name(name) == (verdict == "1"), repr(name)


WINDOWS_PROBE = """
import ctypes, json, sys
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.SetEnvironmentVariableW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
out = [bool(kernel.SetEnvironmentVariableW(name, "v")) for name in json.load(sys.stdin)]
print(json.dumps(out))
"""

POSIX_PROBE = """
import ctypes, json, os, sys
libc = ctypes.CDLL(None, use_errno=True)
libc.setenv.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
out = [libc.setenv(os.fsencode(name), b"v", 1) == 0 for name in json.load(sys.stdin)]
print(json.dumps(out))
"""


def _os_verdicts(names: list[str]) -> list[bool]:
    probe = WINDOWS_PROBE if sys.platform == "win32" else POSIX_PROBE
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        input=json.dumps(names),
        capture_output=True,
        text=True,
        check=True,
    )
    verdicts: list[bool] = json.loads(result.stdout)
    return verdicts


def test_environ_rules_match_the_operating_system() -> None:
    # A C string ends at NUL, so the OS call never sees one; the rule rejects it anyway.
    names = [name for name in _corpus() if "\x00" not in name]
    verdicts = _os_verdicts(names)
    stricter = []
    for name, accepted in zip(names, verdicts, strict=True):
        ours = is_valid_env_name(name, rules="environ")
        if ours:
            assert accepted, repr(name)
        elif accepted:
            stricter.append(name)
    # Windows lets a name start with "=" (the hidden per-drive "=C:" variables) even
    # though its documentation forbids "=" in names; the rule follows the documentation.
    if sys.platform == "win32":
        assert stricter
        assert all(name.startswith("=") and "=" not in name[1:] for name in stricter)
    else:
        assert stricter == []


PUTENV_PROBE = """
import json, os, sys
out = []
for name in json.load(sys.stdin):
    try:
        os.putenv(name, "v")
    except (ValueError, OSError):
        out.append(False)
    else:
        out.append(True)
print(json.dumps(out))
"""


def test_environ_rules_match_python_putenv() -> None:
    # CPython refuses an empty name, "=" anywhere (Windows refuses a leading "=" too,
    # through its C runtime) and NUL; the environ rule set says the same.
    names = [*_corpus(), "A\x00B", "\x00", "=", "=="]
    result = subprocess.run(
        [sys.executable, "-I", "-c", PUTENV_PROBE],
        input=json.dumps(names),
        capture_output=True,
        text=True,
        check=True,
    )
    verdicts = json.loads(result.stdout)
    for name, accepted in zip(names, verdicts, strict=True):
        assert is_valid_env_name(name, rules="environ") == accepted, repr(name)
