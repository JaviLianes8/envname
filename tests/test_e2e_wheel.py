"""Build the sdist and wheel, inspect them, install the wheel in a throwaway venv and
drive the installed package and its command line as an outside consumer would.

Slow and needs the build backend, so it runs only with ENVNAME_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
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
assert importlib.metadata.version("envname") == envname.__version__ == "1.0.0"
assert importlib.resources.files("envname").joinpath("py.typed").is_file()
assert sorted(envname.__all__) == [
    "InvalidEnvName", "Rules", "check_env_name", "is_valid_env_name", "sanitize_env_name"
]
assert is_valid_env_name("PATH") and not is_valid_env_name("path", rules="portable")
assert is_valid_env_name("ProgramFiles(x86)", rules="environ")
assert sanitize_env_name(text="Cr\\u00e8me", prefix="app_") == "APP_CREME"
try:
    check_env_name("MY-VAR")
except InvalidEnvName as exc:
    again = pickle.loads(pickle.dumps(exc))
    assert (again.index, str(again)) == (2, str(exc))
else:
    raise AssertionError("invalid name accepted")
print("e2e ok")
"""

WHEEL_FILES = {
    "envname/__init__.py",
    "envname/__main__.py",
    "envname/_cli.py",
    "envname/_rules.py",
    "envname/_sanitize.py",
    "envname/py.typed",
}


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("dist")
    built = _run(sys.executable, "-m", "build", "--outdir", folder, ROOT)
    assert built.returncode == 0, built.stderr
    return folder


def test_wheel_holds_the_package_license_and_metadata(dist: Path) -> None:
    (wheel,) = dist.glob("envname-1.0.0-py3-none-any.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata = archive.read("envname-1.0.0.dist-info/METADATA").decode()
        entry_points = archive.read("envname-1.0.0.dist-info/entry_points.txt").decode()
    info = {name for name in names if name.startswith("envname-1.0.0.dist-info/")}
    assert names - info == WHEEL_FILES
    assert "envname-1.0.0.dist-info/licenses/LICENSE" in info
    assert "envname = envname._cli:main" in entry_points
    assert "Classifier: Development Status :: 5 - Production/Stable" in metadata
    assert "Requires-Python: >=3.10" in metadata
    assert {line for line in metadata.splitlines() if line.startswith("Requires-Dist")} == {
        f"Requires-Dist: {tool}; extra == 'dev'"
        for tool in ("ruff", "mypy", "pytest", "pytest-timeout", "build", "twine")
    }


def test_sdist_holds_sources_and_tests_but_no_fetched_files(dist: Path) -> None:
    (sdist,) = dist.glob("envname-1.0.0.tar.gz")
    with tarfile.open(sdist) as archive:
        names = {name.split("/", 1)[1] for name in archive.getnames() if "/" in name}
    for required in ("LICENSE", "README.md", "GUIDE.md", "CHANGELOG.md", "pyproject.toml"):
        assert required in names, required
    assert {f"src/{name}" for name in WHEEL_FILES} <= names
    assert "tests/upstream/MANIFEST.json" in names
    assert "scripts/fetch_upstream.py" in names
    for name in names:
        assert "__pycache__" not in name and not name.endswith(".pyc"), name
        assert not name.startswith(("CERT-1.0", "IMPROVEMENTS", "dist/", ".venv")), name
        assert not name.startswith("tests/upstream/") or name.endswith("MANIFEST.json"), name


def test_installed_wheel_end_to_end(dist: Path, tmp_path: Path) -> None:
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

    # The console script is installed and keeps its exit codes and output.
    script = bindir / "envname"
    assert _run(script, "--version", cwd=work).stdout == "envname 1.0.0\n"
    assert _run(script, "check", "PATH", "_x", cwd=work).returncode == 0
    failed = _run(script, "check", "1A", "--", "-x", cwd=work)
    assert failed.returncode == 1
    assert failed.stderr.splitlines() == [
        "envname: invalid shell environment variable name '1A': it starts with a digit at index 0",
        "envname: invalid shell environment variable name '-x': '-' is not allowed at index 0",
    ]
    assert _run(script, "check", "--rules", "environ", "my-var", cwd=work).returncode == 0
    usage = _run(script, "check", "--rules", "posix", "A", cwd=work)
    assert usage.returncode == 2 and "invalid choice: 'posix'" in usage.stderr
    sanitized = _run(script, "sanitize", "--prefix", "APP_", "db.host", "1st", cwd=work)
    assert sanitized.stdout.splitlines() == ["APP_DB_HOST", "APP_1ST"]
    bad_prefix = _run(script, "sanitize", "--prefix", "1-", "x", cwd=work)
    assert bad_prefix.returncode == 2 and bad_prefix.stdout == ""
    module = _run(python, "-m", "envname", "sanitize", "--keep-case", "x.y", cwd=work)
    assert module.stdout == "x_y\n"
