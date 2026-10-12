# envname improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Rule sets: `shell`, `portable`, `environ`, with a typed `Rules` literal
- [x] `check_env_name` and `InvalidEnvName` with the reason and the offending index
- [x] Sanitizer: transliteration, `prefix`, guaranteed valid output, strict input types
- [x] Command line: `envname check` and `envname sanitize`
- [x] Contracts: real shell and real OS ground truth, typing, README examples, installed wheel e2e
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` has `is_valid_env_name` (shell name grammar) and `sanitize_env_name`. Reading it
against the sources below turned up these gaps:

- Only one notion of "valid". POSIX itself has three: the shell `name` grammar, the
  stricter set the standard utilities use (upper case only), and what the environment can
  actually hold (anything without `=`). A tool that reads names from the real environment
  needs the third; a tool that writes names for others needs the second.
- A yes or no answer gives the caller nothing to put in an error message.
- `sanitize_env_name("Ünïcødé")` gives `_N_C_D_`: every accented letter is thrown away.
- No way to namespace generated names (`APP_` prefix), the most common use.
- `is_valid_env_name(None)` and `sanitize_env_name(b"x")` fail with an unrelated error
  from `re`.
- The README claims "POSIX rules" without saying which ones, and nothing ties the claim
  to a real shell or a real operating system.
- Packaging: no keywords, no Python version classifiers, no wheel test.

## Sources (fetched 2026-10-12)

- POSIX.1-2024 XBD 8.1, https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap08.html:
  environment strings have the form name=value and names shall not contain `=`; names used
  by the standard utilities consist solely of uppercase letters, digits and `_` from the
  portable character set and do not begin with a digit; other names may be permitted and
  applications shall tolerate them; case is significant; lowercase names are reserved for
  applications; names starting with a digit are not recommended anywhere.
- POSIX.1-2024 XBD 3.216 Name, https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap03.html:
  in the shell, a word of underscores, digits and alphabetics from the portable character
  set, not starting with a digit.
- POSIX `setenv`, https://pubs.opengroup.org/onlinepubs/9799919799/functions/setenv.html:
  fails with EINVAL when the name is empty or contains `=`.
- Bash manual, https://www.gnu.org/software/bash/manual/bash.html: a name is a word of
  letters, numbers and underscores beginning with a letter or underscore.
- Windows, https://learn.microsoft.com/en-us/windows/win32/procthread/environment-variables:
  the name cannot include `=`; a user-defined variable is at most 32,767 characters.
  `SetEnvironmentVariableW`, https://learn.microsoft.com/en-us/windows/win32/api/processenv/nf-processenv-setenvironmentvariablew.
- Python `os.environ`, https://docs.python.org/3/library/os.html: on Windows keys are
  converted to upper case.
- python-dotenv parser, https://raw.githubusercontent.com/theskumar/python-dotenv/main/src/dotenv/parser.py:
  an unquoted key is `[^=\#\s]+`, so `.env` files accept keys a shell cannot use.
- Compose interpolation, https://raw.githubusercontent.com/compose-spec/compose-spec/main/12-interpolation.md
  and compose-go `template.go`: `$NAME` only interpolates `[_a-z][_a-z0-9]*`, case-insensitive.

## Probes run on this machine (Windows 11, by hand, not from a source)

- `SetEnvironmentVariableW` rejects an empty name and any `=` after the first character
  (error 87), accepts a leading `=` (the hidden per-drive `=C:` variables), and accepts
  names of 40,000 characters: the 32,767 limit does not apply to the name.
- Windows matches names case-insensitively with its own table: `path` finds `PATH`, `é`
  finds `É`, but `straße` does not find `STRASSE`, `ı` does not find `I`, and `ﬁ` does not
  find `FI`, while Python's `str.upper` folds all of them together. No stdlib mapping
  reproduces the Windows table, so this round promises no Windows case folding.
- `bash --posix` with `LC_ALL=C`: `unset -v NAME` accepts exactly the shell names; `dash`
  accepts `A=B` there, so the contract tests use bash.

## Ranked improvements

1. **Named rule sets.** `rules="shell"` (default, the current grammar), `"portable"` (XBD
   8.1 utility names: upper case, digits, `_`, no leading digit) and `"environ"` (what
   `setenv` and Windows accept: non-empty, no `=`, no NUL). A `Rules` literal type makes a
   typo a type error; at run time an unknown rule raises `ValueError`.
2. **`check_env_name`** returns the name or raises `InvalidEnvName` (a `ValueError`) with
   `name`, `rules`, `reason` and `index` of the first offending character, so callers can
   point at the problem.
3. **A sanitizer that keeps letters.** NFKD transliteration (`Crème brûlée` becomes `CREME_BRULEE`),
   an optional `prefix` that is validated, and an output that is always a valid shell name
   (and portable when upper-cased). Non-string input raises `TypeError`.
4. **Ground truth contracts.** Tests compare `shell` with a real `bash --posix`, and
   `environ` with the real `SetEnvironmentVariableW` (Windows) or `setenv` (POSIX).
5. **Command line.** `envname check NAME...` (exit status 1 on any invalid name, reason on
   stderr) and `envname sanitize TEXT...`, for shell scripts and Makefiles.
6. **Typed public API, proven.** mypy runs on a snippet in the suite.
7. **Docs with runnable examples.** Every README block runs in the suite with its output
   pinned; a table explains the three rule sets and when to use each.
8. **Packaging.** Keywords, classifiers, console script, version agreement, installed
   wheel e2e test.

Left out on purpose: Windows case folding (see probes), camelCase splitting and `.env`
file linting (both need policy choices this small library should not make).
