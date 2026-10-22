# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-22

The first release on PyPI (0.1.0 and 0.2.0 were never uploaded there). The public API
is now stable and follows Semantic Versioning: the five names in `__all__`, their
parameter names and defaults, the three rule sets, the error types and their
attributes, and the command line with its exit codes.

### Changed

- `sanitize_env_name` names its first parameter `text` (it was `s`). A value that is
  not a string raises `TypeError: text must be str, not ...`.
- Error messages quote at most the first 60 characters of a name and then give its
  length, so a huge name cannot flood a log; `InvalidEnvName.name` keeps the whole name.
  An unknown `rules` value that is not a string is named by its type, never by its
  `repr`.
- Error messages stop quoting a name before its first `=`: in 0.2.0
  `check_env_name("API_KEY=s3cret", rules="environ")` and `envname check
  DB_PASSWORD=...` printed the value, often a secret. The same holds for an invalid
  `prefix` and an unknown `rules` string.
- `repr(InvalidEnvName)` quotes the name the same way as the message. In 0.2.0 it held
  the whole name, however large, and anything after an `=`.
- `sanitize_env_name` raises `TypeError` when `upper` is not a `bool`. In 0.2.0 any
  object was used for its truth value, so `upper="false"` upper-cased the name.
- `envname sanitize` exits 141 without a traceback when the reader of its output goes
  away early (`| head -1`); in 0.2.0 it printed a traceback and exited 1 or 120.
- Command line usage errors quote at most 300 characters of the offending argument,
  and an unknown `--rules` value at most 60. In 0.2.0 argparse repeated it in full.
- The public objects report `envname` as their module, so a pickled `InvalidEnvName`
  and `help()` no longer depend on the private module layout.

### Fixed

- `sanitize_env_name` takes time in proportion to the length of the text. In 0.2.0 a
  long run of combining marks (zalgo text) or a repeated U+FDFA took quadratic time:
  over 30 seconds for 200,000 characters. The names it returns are unchanged.

### Added

- `envname --version`.
- A runnable example in every public docstring, checked as a doctest, and a
  [guide](https://github.com/JaviLianes8/envname/blob/main/GUIDE.md) with the full
  reference.

## [0.2.0] - 2026-10-12

Committed as 4583912 and never uploaded to PyPI.

### Added

- `rules=` on `is_valid_env_name`: `"shell"` (the default, unchanged), `"portable"`
  (upper case, the names the POSIX utilities use) and `"environ"` (anything the
  environment can hold: not empty, no `=`, no NUL). The `Rules` type names them.
- `check_env_name` returns a valid name and raises `InvalidEnvName`, a `ValueError` with
  `name`, `rules`, `reason` and `index`, for an invalid one. It pickles and copies.
- `sanitize_env_name(prefix=...)` puts a validated prefix in front of the name.
- `envname check` and `envname sanitize` on the command line, also as `python -m envname`.

### Changed

- `sanitize_env_name` folds accented letters, ligatures and full-width forms to ASCII
  (`"Crème"` becomes `"CREME"`, it used to become `"CR_ME"`).
- A name or text that is not a string raises `TypeError` with a clear message, and an
  unknown rule set raises `ValueError`.

## [0.1.0] - 2026-10-11

Committed as eb89a38 and never uploaded to PyPI.

### Added

- Add `is_valid_env_name` to check a string against POSIX environment name rules.
- Add `sanitize_env_name` to turn any string into a valid environment name.

[Unreleased]: https://github.com/JaviLianes8/envname/commits/main
[1.0.0]: https://github.com/JaviLianes8/envname/compare/4583912...main
[0.2.0]: https://github.com/JaviLianes8/envname/compare/eb89a38...4583912
[0.1.0]: https://github.com/JaviLianes8/envname/commit/eb89a38
