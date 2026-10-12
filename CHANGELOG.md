# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

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

## [0.1.0]

- Add `is_valid_env_name` to check a string against POSIX environment name rules.
- Add `sanitize_env_name` to turn any string into a valid environment name.
