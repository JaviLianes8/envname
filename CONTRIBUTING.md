# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/envname/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing. Two deliberate exceptions: `tests/test_ground_truth.py`
  asks a real `bash` and the real operating system (in a child process), and the opt-in
  `tests/test_e2e_wheel.py` builds the wheel, which needs network for the build backend.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes. Set
  `ENVNAME_E2E=1` to also build the wheel and test it installed.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
