# envname 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to envname. Nothing is on PyPI yet
(`https://pypi.org/pypi/envname/json` answered 404 on 2026-10-22, and so did the
similar names `env-name`, `env_name` and `env.name`), so 1.0.0 is the first upload and
there is no upgrade path to check. Every change is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (4583912, version 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: fetched specifications, Unicode data, real programs (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] PR and trace guard
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Baseline on 0.2.0 (before any change)

Fresh clone of `release/1.0.0` at 4583912 on another machine, CPython 3.14.2:
`ruff format --check .`, `ruff check .` and `mypy --strict src tests` exit 0; `pytest`
141 passed, 2 skipped (the installed-wheel test, which needs `ENVNAME_E2E=1`, and the
bash ground truth, as that machine has no `bash` on its `PATH`).
