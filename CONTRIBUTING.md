# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/envname/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing. Deliberate exceptions: `tests/test_ground_truth.py` asks a
  real `bash`, the real operating system and `os.putenv` (each in a child process), and
  the opt-in `tests/test_e2e_wheel.py` builds the sdist and wheel, which needs network
  for the build backend.
- `python scripts/fetch_upstream.py` downloads the specifications, Unicode data and
  upstream sources listed in `tests/upstream/MANIFEST.json`. They are not committed;
  their tests skip until the files are there and fail if a file differs from the
  manifest.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes. Set
  `ENVNAME_E2E=1` to also build the packages and test the installed wheel.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
