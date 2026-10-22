# envname 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to envname. Nothing is on PyPI yet
(`https://pypi.org/pypi/envname/json` answered 404 on 2026-10-22, and so did the
similar names `env-name`, `env_name` and `env.name`), so 1.0.0 is the first upload and
there is no release to upgrade from. Every change against 0.2.0 is still in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (4583912, version 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: fetched specifications, Unicode data, real programs (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [x] PR #3 and trace guard CLEAN
- [x] QA lenses round 1: every finding fixed at 7b0ddad (none disputed)
- [x] QA lenses round 2: every finding fixed at 9b27a1e (none disputed)
- [x] QA lenses round 3: every finding fixed at b553ca7 (none disputed)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 5 names; `sanitize_env_name(text, ...)` renamed from `s`; signatures pinned by `tests/test_contract_api.py` |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: 5 doctests in the package, README (16 outputs, 3 commands) and GUIDE (15 examples) run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, typing checked from a consumer snippet |
| 5 | Typed, documented, bounded errors | PASS: `InvalidEnvName` (a `ValueError`), `TypeError`, `ValueError`; messages and `repr` quote at most 60 characters and nothing from the first `=` on (QA round 1) |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: 13 fetched sources with a hash manifest; bash, the OS call, `os.putenv`, python-dotenv run live |
| 8 | Real e2e from the wheel | PASS: sdist and wheel built and inspected, wheel installed in a fresh venv, API and CLI driven from an empty folder; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t |
| 11 | README and `twine check` | PASS: `twine check --strict`, absolute links |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-22 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending |
| 17 | PR and trace guard | PR #3 from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author round 32 mutants, 32 killed after two contracts were added |
| 19 | Five independent QA lenses | pending |

## Baseline on 0.2.0 (before any change)

Fresh clone at 4583912 on another machine, CPython 3.14.2: `ruff format --check .`,
`ruff check .` and `mypy --strict src tests` exit 0; `pytest` 141 passed, 2 skipped (the
installed-wheel test, which needs `ENVNAME_E2E=1`, and the bash ground truth, as that
machine has no `bash` on its `PATH`).

Gaps found in 0.2.0 by running it: an `InvalidEnvName` message quoted the whole name (a
1 MB name gave a 1 MB message); an unknown `rules` object was shown with its `repr`
(which can be huge or raise); the first parameter of `sanitize_env_name` was called `s`;
pickles and tracebacks named the private module `envname._rules`; no docstring had an
example; README links to LICENSE were relative; there was no guide, no fuzzing beyond
the sanitizer, and no fetched source behind the rule sets.

## API review (item 1)

Kept: `is_valid_env_name(name, *, rules="shell")`, `check_env_name(name, *,
rules="shell")`, `InvalidEnvName(name, rules, reason, index=None)` with its four
attributes, the `Rules` literal and the command line. Changed, all in the CHANGELOG:
`sanitize_env_name(text, *, upper=True, prefix="")` (was `s`), bounded messages, unknown
rules named by type, public objects report the module `envname`. Added: `envname
--version`. The GUIDE states the stability promise (the wording of reasons may improve;
the attributes are stable).

## Ground truth (item 7)

Fetched on 2026-10-22 by `scripts/fetch_upstream.py` into the ignored `tests/upstream`
folder; `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence,
and the tests check the hash before reading. Nothing fetched is committed or shipped.

- POSIX.1-2024 XBD chapters 3, 6 and 8 and XSH `setenv` (`tests/test_spec_sources.py`):
  the 3.216 Name and 8.1 utility-name sentences are cut from the text; the letter, digit
  and underscore classes are read from the 6.1 Portable Character Set table (by the
  character descriptions) and compared with both rule sets on every code point up to
  U+02FF plus separators, a surrogate, full-width and astral characters, in first and
  later position; all 24 variables defined in chapter 8 and the 77 names of its "unwise
  to conflict" table are `portable`; the `=`, empty and NUL rules for `environ` are tied
  to the XBD 8.1, `setenv` and Windows sentences.
- Bash manual: the `name` definition is cut from the text.
- Unicode Character Database 13.0.0 to 16.0.0 (`tests/test_unicode_data.py`): for the
  version of the running Python, the expected sanitized form of every assigned code
  point, every range boundary and every 251st code point (over 30,000 characters) is
  rebuilt from the decomposition mappings and general categories in `UnicodeData.txt`,
  independently of `unicodedata`; every mark between two letters is dropped.
- Real programs: `bash` (`unset -v` on 1,000+ generated names, one shell), the call that
  stores a variable (`SetEnvironmentVariableW` on Windows, `setenv` on POSIX) and
  `os.putenv` agree with `shell` and `environ` (`tests/test_ground_truth.py`);
  python-dotenv 1.1.1 is run on the generated keys and matches the `_unquoted_key`
  pattern read from its fetched `parser.py`; the Compose pattern is read from
  compose-go `template.go` (`tests/test_oracles.py`). The README's "Why" claims run in
  `tests/test_docs.py`.

## Fuzz and hostile input (item 9)

`tests/test_fuzz.py`: three seeds of 4,000 names per rule set over ASCII, separators,
NUL, non-ASCII letters and digits, marks, surrogates and astral characters, compared
with a character-by-character model of each grammar (validity, reason and index all
agree; every message at most 800 characters); three seeds of 4,000 texts for the
sanitizer (valid, stable, prefix law); eight input shapes timed at 20,000 and 200,000
characters through all three rule sets and the sanitizer (linear). A 1,000,001-character
name gives a message under 200 characters (`tests/test_contract_api.py`).

## Author mutation round (item 18)

32 mutants over every module, each applied alone to a clean checkout of 7d1bbd2 on
another machine (fetched sources, Git's `bash` and python-dotenv present, bytecode
writing off), the suite run with `-x` and a 300 s per-test limit. The first run at
7e2841e left two survivors, M08 and M14; the contracts in 7d1bbd2 (non-ASCII leading
digits in `tests/test_check.py` and every reason in the fuzz model; rules given as a
`str` subclass) kill both. Final run: 32 of 32 killed.

| Mutant | Module | Change | Killed by |
| --- | --- | --- | --- |
| M01 | `_rules.py` | shell accepts a leading digit | doctest `envname.is_valid_env_name` |
| M02 | `_rules.py` | shell drops `_` after the first character | doctest `envname.check_env_name` |
| M03 | `_rules.py` | portable accepts a lower-case first letter | `test_fuzz.py::test_every_name_agrees_with_the_model[portable-20261022]` |
| M04 | `_rules.py` | environ accepts NUL | `test_docs.py::test_every_guide_example_runs` |
| M05 | `_rules.py` | environ accepts an empty name | `test_check.py::test_reports_reason_and_first_offending_index[-environ-...]` |
| M06 | `_rules.py` | `is_valid_env_name` matches a prefix only | `test_docs.py::test_every_python_example_prints_the_transcript` |
| M07 | `_rules.py` | offending index off by one | doctest `envname.check_env_name` |
| M08 | `_rules.py` | leading digit tested with `str.isdigit` | `test_check.py::test_reports_reason_and_first_offending_index[\u0663A-shell-...]` |
| M09 | `_rules.py` | empty name reports index 0 | `test_check.py::test_reports_reason_and_first_offending_index[-shell-...]` |
| M10 | `_rules.py` | environ reasons swapped | `test_check.py::test_reports_reason_and_first_offending_index[KEY=VALUE-environ-...]` |
| M11 | `_rules.py` | non-ASCII lower case called "not portable" | `test_check.py::test_reports_reason_and_first_offending_index[A\xe9-portable-...]` |
| M12 | `_rules.py` | quote limit off by one | `test_contract_api.py::test_messages_quote_at_most_sixty_characters` |
| M13 | `_rules.py` | message quotes the whole name | `test_contract_api.py::test_messages_quote_at_most_sixty_characters` |
| M14 | `_rules.py` | rules kept as the caller's `str` subclass | `test_check.py::test_rules_given_as_a_str_subclass_are_stored_as_exact_str` |
| M15 | `_rules.py` | name not copied to an exact `str` | `test_check.py::test_str_subclass_cannot_make_the_explanation_disagree` |
| M16 | `_rules.py` | `ValueError` instead of `TypeError` for a non-string | `test_check.py::test_non_string_raises_type_error` |
| M17 | `_rules.py` | error args do not match `__init__` | `test_contract_api.py::test_error_is_a_value_error_with_its_fields` |
| M18 | `_rules.py` | message drops the index | doctest `envname.check_env_name` |
| M19 | `_rules.py` | unknown rules object shown with `repr` | `test_contract_api.py::test_unknown_rules_raise_value_error_naming_them_safely[None-NoneType]` |
| M20 | `_sanitize.py` | enclosing marks kept | `test_sanitize.py::test_sanitizes[x\u20ddy-XY]` |
| M21 | `_sanitize.py` | NFD instead of NFKD | `test_sanitize.py::test_sanitizes[\ufb01le-FILE]` |
| M22 | `_sanitize.py` | runs not collapsed | `test_docs.py::test_every_python_example_prints_the_transcript` |
| M23 | `_sanitize.py` | leading digit not guarded | doctest `envname.sanitize_env_name` |
| M24 | `_sanitize.py` | `upper` inverted | doctest `envname.sanitize_env_name` |
| M25 | `_sanitize.py` | prefix not validated | `test_cli.py::test_sanitize_rejects_an_invalid_prefix` |
| M26 | `_sanitize.py` | prefix appended | doctest `envname.sanitize_env_name` |
| M27 | `_cli.py` | `check` exits 0 on invalid names | `test_cli.py::test_check_reports_every_invalid_name_and_exits_one` |
| M28 | `_cli.py` | `check` stops at the first invalid name | `test_cli.py::test_check_reports_every_invalid_name_and_exits_one` |
| M29 | `_cli.py` | `--keep-case` inverted | `test_cli.py::test_sanitize_prints_one_name_per_text` |
| M30 | `_cli.py` | unprintable names crash the report | `test_cli.py::test_check_escapes_what_the_console_cannot_show` |
| M31 | `_cli.py` | default rule set `portable` | `test_cli.py::test_check_exits_zero_when_every_name_is_valid` |
| M32 | `__init__.py` | public objects report the private module | `test_contract_api.py::test_public_objects_live_in_the_package` |

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- Full suite at 7d1bbd2 on another machine from a fresh clone, with the fetched sources,
  Git's `bash`, python-dotenv and `ENVNAME_E2E=1`: 211 passed, no skips. The e2e tests
  build the sdist and wheel, check their file lists and metadata, install the wheel in a
  fresh venv and drive the API with `-I` and the console script and `python -m envname`
  from an empty folder.
- Wheel: the six package files plus `METADATA`, `WHEEL`, `RECORD`, `entry_points.txt`
  and `licenses/LICENSE`. Sdist: sources, tests, scripts, docs, LICENSE and the manifest;
  no fetched file, no `CERT-1.0-*`, no `IMPROVEMENTS-round*`, no caches.
  `twine check --strict` passes on both.
- Every interpreter on this PC from `requires-python` up, at 7e2841e (code identical to
  7d1bbd2): the wheel installed in a fresh venv and the sdist's own suite run with `src`
  removed (fetched sources, Git's `bash` and python-dotenv present), package doctests
  included: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded,
  205 passed and 3 skipped each (the e2e tests, which run separately). 3.8 and 3.9 are
  below `requires-python`.

## Gates (item 15)

At 7d1bbd2 on another machine, from a clean checkout with the fetched sources, Git's
`bash`, python-dotenv and `ENVNAME_E2E=1`, each command on its own:
`ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
and `pytest` (211 passed) all exit 0.

## QA lenses (item 19)

### Round 1 (reviewed 68a6f91, fixed in 7b0ddad)

Five lenses: (a) API and docs, (b) correctness and ground truth, (c) adversarial, (d)
packaging and e2e, (e) contract strength. Lens (b) found the library itself agreeing with
every oracle (0 mismatches on over 4 million cases); its one finding was in the README.
Every finding below is fixed; none is disputed. Behaviour fixes were first pinned by a
contract test that failed on 68a6f91.

| Lens | Finding | Severity | Fix |
| --- | --- | --- | --- |
| c | F1: `sanitize_env_name` quadratic on long runs of combining marks and on repeated U+FDFA (whole-text NFKD) | high | `_fold_to_ascii` folds one character at a time (cached), ASCII text skips it; same names, checked against whole-text NFKD on 5,000 mark-heavy texts. `test_fuzz.py` gains the "mixed marks" and "long decomposition" shapes. Before: 10k to 40k characters took 17x and 12x longer; after: 3x and 4x |
| c | F2: messages echo what follows `=` (often a secret), also through the CLI and `prefix` | medium | `_quote` stops before the first `=` and gives the length; `tests/test_messages.py` |
| c | F3: `repr(InvalidEnvName)` holds the whole name | low | `__repr__` quotes the name like the message; pickling keeps the whole name |
| c | F4: CLI repeats an invalid `--rules` value in full | low | `--rules` is checked by a `type=` function with a bounded message; every usage error is cut at 300 characters (unknown command, unrecognised argument too) |
| c, d | F5 / F1: `envname sanitize` traceback when stdout's reader goes away | low | caught (EPIPE, and EINVAL on Windows), stdout pointed at the null device, exit 141; in-process test and a subprocess test with a closed pipe |
| c | F6: `upper` used as a truth value (`"false"` upper-cased) | low | `TypeError: upper must be bool, not ...`, never calls `__bool__` |
| a, d, e | A1 / F2 / F9: documented `fetch_upstream.py` exits 1 (the Microsoft Learn page is served with per-client CDN additions); the Bash manual was pinned the same mutable way | low | the Windows source is the page's markdown at MicrosoftDocs/win32 commit 3aee48a; the Bash manual is `doc/bashref.html` from the bash 5.3 release archive (archive and member both hashed); `tests/test_fetch_upstream.py` pins the script offline and that every source names a fixed revision. A fresh clone of 7b0ddad: fetch exits 0, `test_spec_sources.py` 8 passed, none skipped |
| a | A2: GUIDE message format ignored `index=None` | low | reworded; also documents the `=` cut and the `repr` |
| a | A3: CONTRIBUTING's "never touch the real thing" had unlisted exceptions | low | rule reworded; every test that runs a real program or writes under `tmp_path` is listed |
| a | A4: CHANGELOG 0.1.0 and 0.2.0 undated, no change-type heading, no link definitions | low | dated from git (eb89a38 2026-10-11, 4583912 2026-10-12), `### Added` under 0.1.0, link definitions as in the sibling libraries |
| b | F1: README's Windows length bullet was wrong (the `=` counts; `SetEnvironmentVariableW` stores longer names) | low | reworded to the observed limits; `test_docs.py::test_the_windows_length_limits_are_as_stated` checks them in a child process on Windows (reproduced here on CPython 3.13.2) |
| e | F1 to F8: surviving mutants (underscore runs collapsed, text stripped, output cut at 255, Mc marks dropped, `check`/`sanitize` without arguments, CLI upper-casing the prefix, error holding a `str` subclass) | medium, low | contracts added: `__init__`, `a__b`, `a_-_b`, ` db host `, `	PATH
`, `a` * 300 (both cases), U+093E and U+0903, missing `NAME` and `TEXT` exit 2, `--keep-case --prefix app_`, `type(error.name) is str` for a `str` subclass with its own `__str__` |

Behaviour changes recorded in the CHANGELOG 1.0.0 section: messages and `repr` stop
before `=`, `upper` must be a `bool`, exit 141 on a closed pipe, bounded usage errors,
and the linear-time fix.

Verification at 7b0ddad:

- This PC, a clean export with the fetched sources, Git's `bash` and python-dotenv, one
  interpreter at a time: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2
  free-threaded each 248 passed, 3 skipped (the opt-in wheel e2e).
- Another machine, CPython 3.14.2, with `ENVNAME_E2E=1`: `ruff format --check .`,
  `ruff check .`, `mypy --strict src`, `mypy --strict src tests` and `pytest` each exit 0;
  250 passed, 1 skipped (no `bash` there).

### Round 2 (reviewed 5b635dd, fixed in 9b27a1e)

Lens (b) reported no finding. Lenses (a) and (c) re-verified every round 1 fix at 5b635dd
(fresh clone fetch 13/13, linear sanitize, no secret after `=`, bounded errors, exit 141).
Every finding below is fixed; none is disputed. The behaviour bug was first pinned by a
contract test that failed on 5b635dd (`AttributeError`, exit 1).

| Lens | Finding | Severity | Fix |
| --- | --- | --- | --- |
| c, d | N1: `envname sanitize` with no stdout at all (`>&-`, `pythonw`) crashed in `sys.stdout.flush()` with `AttributeError` and exit 1 (0.2.0 exited 0); a regression of the round 1 pipe fix | low | `_print_lines` returns 0 when `sys.stdout` is None. `tests/test_cli_contract.py`: in-process with `sys.stdout = None`, and a child started by `bash` with `>&-` that must exit 0 with empty stderr. CHANGELOG and GUIDE say so |
| a | A5: CHANGELOG's "over 30 seconds for 200,000 characters" held only for the worst order of marks | low | the absolute figure is dropped; the entry says the time grew with the square of the length |
| e | G1 (N11): nothing pinned that an unknown `--rules` value is quoted up to its `=` and 60 characters | medium | exact last line for `--rules TOKEN=hunter2` (no `hunter2`) and for a 200-character value |
| e | G2 (N22): nothing pinned that a write error other than a gone reader propagates | medium | a stdout raising `ENOSPC` must raise `OSError` with that errno, never exit 141 |
| e | G3 (N15, N16, N18): the 300-character cap on usage errors was only bounded below 1000 | medium | exact last line for messages of 300 (whole), 301 and 2066 characters (cut at 300 plus `... (N characters)`); GUIDE states the cut |
| e | G4 (N10): `repr` of an `InvalidEnvName` subclass | low | `repr(Mine(...))` starts with `Mine(` in `test_repr_is_as_short_as_the_message` |
| e | G5 (N14): GUIDE synopsis not tied to `check --help` | low | the usage line must contain `[--rules {shell,portable,environ}]` and the GUIDE synopsis line must be present |
| e | G6 (N33, N36, N39): `fetch_upstream.py --update` and the size-and-sha256 check untested | low | an `--update` test (files saved; `size`, `sha256`, `archive_*` and `fetched` rewritten in MANIFEST.json) and a refusal of same-size bytes with another sha256 |

Every surviving mutant reported in this round was re-applied one at a time to 9b27a1e and
is now killed: N1, N11, N22, N15, N16, N18, N14 by `test_cli_contract.py`, N10 by
`test_messages.py`, N33, N36, N39 by `test_fetch_upstream.py`.

Verification at 9b27a1e:

- This PC: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` exit 0.
- Another machine, CPython 3.14.2, clean clone with the fetched sources, Git's `bash`,
  python-dotenv and `ENVNAME_E2E=1`: `pytest` exits 0, 261 passed, 1 skipped (one fetched
  file was not copied there); that file's tests, `test_spec_sources.py`, pass here, 8
  passed.

### Round 3 (reviewed 21c6ba2, fixed in b553ca7)

Lenses (c) and (d) both re-verified N1 (no stdout) as fixed on every interpreter and found
no regression of round 1 or 2; both reported the same new finding, its stderr twin. Fixed;
none is disputed. It was first pinned by `tests/test_cli_streams.py`, which fails on
21c6ba2: 9 of its 30 tests on CPython 3.13.2, 18 on 3.10.19.

| Lens | Finding | Severity | Fix |
| --- | --- | --- | --- |
| c, d | N2: a process started without a stderr (`2>&-`, `pythonw`). `_warn` wrote to `sys.stderr` unguarded, so `main(["check", "1X"])` raised `AttributeError` instead of returning 1 (and `python -m envname` raised it instead of `SystemExit(1)`; the process exited 1 only because the exception was unhandled). On 3.10, argparse also wrote to the missing stream, so a usage error exited 1 instead of 2 and `--version` under `pythonw` exited 1 instead of 0 | low | `_warn` returns at once without a stderr. `_Parser._print_message` skips a missing stream and a write `OSError`, as argparse does from 3.11. Fixing it showed a further wart on every version: without a stderr, argparse prints the usage line of an error on stdout instead (where `sanitize` prints names), so `_Parser.error` now exits 2 at once when there is no stderr. Tests, each over 7 command lines (valid and invalid `check`, bad `--prefix`, unknown `--rules`, missing `TEXT`, `--version`, `sanitize`): in-process with `sys.stderr = None` (exit status and the exact stdout), with both streams None, a child started by `bash` with `2>&-` (exact stdout and status), and a child started by `pythonw` with no standard handles; plus `runpy` as `__main__` exits 1, and a stderr raising `ENOSPC` still gives exit 2. GUIDE and CHANGELOG say so |

Verification at b553ca7:

- This PC: `ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
  and `pytest` exit 0.
- This PC, wheel built from a clean clone (`twine check --strict` passed) and installed in a
  fresh venv per interpreter, the sdist's suite with Git's `bash`: CPython 3.10.19, 3.11.5,
  3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded each 288 passed, 4 skipped (the opt-in
  wheel e2e and one fetched file not copied).
- Another machine, CPython 3.14, clean clone with the fetched sources, Git's `bash`,
  python-dotenv and `ENVNAME_E2E=1`: `pytest` exits 0, 291 passed, 1 skipped (one fetched
  file was not copied there).

### Round 4 (reviewed d04c5c1, fixed in 0a50825)

Lenses (c) and (d) both re-verified N2 (no stderr) as fixed: in process, under `2>&-` and
under `pythonw`, on 3.10 to 3.14 and 3.14t, wheel- and sdist-installed, with no regression
of F1 to F6 or N1. Both reported the same new finding in two halves (lens c N3 and N4, lens
d N3): a stream that exists but whose reader has gone. Not a regression (0.2.0 exits 120
too, checked here on 3.10.19 and 3.13.2), but 1.0.0 promised the status survives a lost
message. Fixed; none is disputed. It was first pinned by `tests/test_cli_gone_reader.py`,
which fails on d04c5c1: 10 of its 14 tests on CPython 3.13.2.

| Lens | Finding | Severity | Fix |
| --- | --- | --- | --- |
| c, d | c N3 / d N3: `_warn` had no `OSError` handling, so `check 1A` with the stderr reader gone raised `BrokenPipeError` (EINVAL on Windows) out of `main()`, stopped checking, and the process exited 120 instead of 1 | low | `_warn` writes and flushes inside `try`; on a gone reader (EPIPE, or EINVAL on Windows) it points the stream's descriptor at the null device and tells `main` to stop reporting, which keeps checking and returns 1 (or 0). Any other write error, such as `ENOSPC`, still propagates, as on stdout. Shared helpers `_reader_gone` and `_to_null` now serve `_print_lines` too |
| c, d | c N4 / d N3: `_Parser._print_message` swallowed the write `OSError` but left the text in the stream buffer, so the flush at interpreter shutdown failed and the process exited 120: a usage error with the stderr reader gone (GUIDE: 2), `--help` and `--version` with the stdout reader gone (GUIDE: 0, plus `Exception ignored ... OSError` on stderr) | low | `_print_message` writes and flushes inside `try`; on any `OSError` it points the stream's descriptor at the null device, so the shutdown flush succeeds: 2 for usage errors, 0 for `--help` and `--version`. The in-memory `ENOSPC` contract from round 3 still passes |

Tests (`tests/test_cli_gone_reader.py`): a child started with the read end of its pipe
already closed, on stderr for `check PATH` (0), `check 1A` (1), `check` with 3000 invalid
names and one valid (1), a bad `--prefix`, `--bogus` and an unknown command (2), and on
stdout for `--version`, `--help`, `check --help` (0) and `sanitize` (141, the control);
each must also leave the other stream empty (no usage line, no `Exception ignored`). In
process: a stderr raising `BrokenPipeError`, and EINVAL with the platform set to Windows,
is written once and `main` returns 1; a stderr raising `ENOSPC` still raises; `--help` with
a gone stdout reader exits 0. GUIDE and CHANGELOG say so.

Verification of the fix:

- This PC: lens (d)'s `brokenpipe.py` (7 cases) passes 7 of 7 on CPython 3.10.19, 3.11.5,
  3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded (on the 0.2.0 source it fails 6 of 7,
  with 120 for each broken stream). Lens (c)'s git-bash repros print 1 for
  `check 1X 2>&1 | head -c 0`, 0 for `--help 2>/dev/null | head -c 0`, 2 for `--bogus`
  and 141 for `sanitize`. `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` exit 0.
- Another machine, CPython 3.14.2, the working tree with the fetched sources, Git's `bash`,
  python-dotenv and `ENVNAME_E2E=1`, each command on its own: `ruff format --check .`,
  `ruff check .`, `mypy --strict src`, `mypy --strict src tests` and `pytest` exit 0; 306
  passed, none skipped.

### Disputed findings

None in rounds 3 and 4.

Round 5 verdicts: pending.

## Independent review (item 16)

Pending.
