"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with ENVNAME_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("ENVNAME_E2E") != "1", reason="set ENVNAME_E2E=1 to build and install"
)

PROGRAM = """
import importlib.metadata, importlib.resources, pickle
import envname
from envname import InvalidEnvName, check_env_name, is_valid_env_name, sanitize_env_name

assert "site-packages" in envname.__file__, envname.__file__
assert importlib.metadata.version("envname") == envname.__version__
assert importlib.resources.files("envname").joinpath("py.typed").is_file()
assert is_valid_env_name("PATH") and not is_valid_env_name("path", rules="portable")
assert is_valid_env_name("ProgramFiles(x86)", rules="environ")
assert sanitize_env_name("Cr\u00e8me", prefix="app_") == "APP_CREME"
try:
    check_env_name("MY-VAR")
except InvalidEnvName as exc:
    assert pickle.loads(pickle.dumps(exc)).index == 2
else:
    raise AssertionError("invalid name accepted")
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("envname-*.whl")

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"

    # The console script is installed and keeps its exit codes.
    script = bindir / "envname"
    assert _run(script, "check", "PATH", cwd=work).returncode == 0
    failed = _run(script, "check", "1A", cwd=work)
    assert failed.returncode == 1
    assert "it starts with a digit" in failed.stderr
    sanitized = _run(script, "sanitize", "--prefix", "APP_", "db.host", cwd=work)
    assert sanitized.stdout == "APP_DB_HOST\n"
    module = _run(python, "-m", "envname", "sanitize", "x.y", cwd=work)
    assert module.stdout == "X_Y\n"
