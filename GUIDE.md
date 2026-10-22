# envname guide

The full reference for envname 1.0. The
[README](https://github.com/JaviLianes8/envname/blob/main/README.md) is the short tour.
Every example on this page runs in the test suite.

- [Rule sets](#rule-sets)
- [is_valid_env_name](#is_valid_env_name)
- [check_env_name](#check_env_name)
- [InvalidEnvName](#invalidenvname)
- [sanitize_env_name](#sanitize_env_name)
- [Command line](#command-line)
- [Stability](#stability)
- [Sources](#sources)

## Rule sets

`Rules` is `Literal["shell", "portable", "environ"]`, so a type checker rejects a
misspelt rule set. At run time an unknown value raises `ValueError`.

| `rules` | A valid name | Reject reasons, in the order they are checked |
| --- | --- | --- |
| `"shell"` (default) | `[A-Za-z_][A-Za-z0-9_]*` | empty, a leading digit, then the first character outside the set |
| `"portable"` | `[A-Z_][A-Z0-9_]*` | the same, and a lower-case ASCII letter is named as such |
| `"environ"` | not empty, no `=`, no NUL | empty, then the first `=` or NUL |

Only ASCII letters and digits count, as in the C locale: `é`, the full-width `Ａ` and
the Arabic-Indic digit `٣` are outside every set but `environ`. Names are compared case
sensitively. `portable` names are `shell` names, and `shell` names are `environ` names.

```pycon
>>> from envname import is_valid_env_name
>>> [is_valid_env_name("Home", rules=rules) for rules in ("shell", "portable", "environ")]
[True, False, True]
>>> is_valid_env_name("été"), is_valid_env_name("été", rules="environ")
(False, True)

```

## is_valid_env_name

`is_valid_env_name(name: str, *, rules: Rules = "shell") -> bool`

Answers yes or no. A `str` subclass is accepted and judged by its characters.

- `TypeError` when `name` is not a `str`: `name must be str, not bytes`.
- `ValueError` when `rules` is not one of the three names. The message quotes a string
  value (at most 60 characters of it) and names any other value by its type only.

```pycon
>>> is_valid_env_name("KEY=VALUE", rules="environ")
False
>>> is_valid_env_name(b"PATH")
Traceback (most recent call last):
    ...
TypeError: name must be str, not bytes
>>> is_valid_env_name("PATH", rules="posix")
Traceback (most recent call last):
    ...
ValueError: rules must be one of 'shell', 'portable', 'environ', not 'posix'

```

## check_env_name

`check_env_name(name: str, *, rules: Rules = "shell") -> str`

Returns the name as an exact `str` when it is valid, and raises `InvalidEnvName` when it
is not. `TypeError` and `ValueError` as for `is_valid_env_name`. The two functions
always agree: `check_env_name` raises exactly when `is_valid_env_name` returns False.

```pycon
>>> from envname import InvalidEnvName, check_env_name
>>> check_env_name("LC_ALL", rules="portable")
'LC_ALL'
>>> for name, rules in [
...     ("", "shell"),
...     ("9A", "shell"),
...     ("A.B", "shell"),
...     ("Path", "portable"),
...     ("A=B", "environ"),
...     ("A\0B", "environ"),
... ]:
...     try:
...         check_env_name(name, rules=rules)
...     except InvalidEnvName as error:
...         print(repr(error.reason), error.index)
'it is empty' None
'it starts with a digit' 0
"'.' is not allowed" 1
"lower-case 'a' is not portable" 1
"'=' separates the name from the value" 1
'NUL ends the string early' 1

```

## InvalidEnvName

A `ValueError` with four attributes:

- `name`: the whole name that failed, however long.
- `rules`: the rule set it was checked against.
- `reason`: a short explanation, as listed above.
- `index`: the position of the first offending character, or None for an empty name.

The message is `invalid <rules> environment variable name <name>: <reason>`, followed by
` at index <index>` unless `index` is None. The quoted name stops before its first `=`,
since what follows is usually a value and often a secret, and is cut at 60 characters;
when anything is left out, the message gives the full length instead, so a huge name
cannot flood a log. `repr(error)` quotes the name the same way. The error pickles and
copies with every attribute, and its pickle refers to `envname.InvalidEnvName`.

```pycon
>>> try:
...     check_env_name("X" * 100 + "-")
... except InvalidEnvName as error:
...     print(len(error.name), error.index)
...     print(str(error).split("... ")[1])
101 100
(101 characters): '-' is not allowed at index 100
>>> try:
...     check_env_name("API_KEY=s3cret", rules="environ")
... except InvalidEnvName as error:
...     print(error)
invalid environ environment variable name 'API_KEY'... (14 characters): '=' separates the name from the value at index 7

```

## sanitize_env_name

`sanitize_env_name(text: str, *, upper: bool = True, prefix: str = "") -> str`

Turns any text into a valid name, in this order:

1. Unicode NFKD decomposition, then every nonspacing and enclosing mark (general
   category Mn or Me) is dropped. Accented letters keep their base letter (`é` to `e`),
   ligatures and full-width forms become plain letters (`ﬁ` to `fi`, `Ａ` to `A`).
2. Every run of characters outside `[A-Za-z0-9_]` becomes one `_`; underscores already in
   the text are kept as they are. Letters with no ASCII decomposition, such as `ß`, `ø` or
   any CJK character, end up there, and so do spacing marks (category Mc) and
   whitespace, including at the ends of the text.
3. `prefix` goes in front. It must be empty or a valid `shell` name, or the call raises
   `InvalidEnvName`.
4. An `_` goes in front when the result is empty or starts with a digit.
5. The result is upper-cased unless `upper=False`.

The result is always a valid `shell` name, and a valid `portable` one when upper-cased.
Upper-cased output passes through unchanged, so sanitizing twice changes nothing.
Nothing is cut: the result is as long as the text needs. The time taken grows in
proportion to the length of the text, whatever it holds.
`TypeError` when `text` or `prefix` is not a `str`, or when `upper` is not a `bool`
(`upper="false"` is an error, not a true value).

```pycon
>>> from envname import sanitize_env_name
>>> sanitize_env_name("Straße 1")
'STRA_E_1'
>>> sanitize_env_name("", prefix="APP"), sanitize_env_name("")
('APP', '_')
>>> sanitize_env_name("x", prefix="1APP")
Traceback (most recent call last):
    ...
envname.InvalidEnvName: invalid shell environment variable name '1APP': it starts with a digit at index 0

```

## Command line

```
envname check [--rules {shell,portable,environ}] NAME...
envname sanitize [--keep-case] [--prefix PREFIX] TEXT...
envname --version
```

`python -m envname` is the same program.

- `check` prints nothing and exits 0 when every name is valid. Otherwise it prints one
  line per invalid name on stderr, `envname: <message>`, and exits 1. Characters the
  console cannot show are escaped rather than crashing the report.
- `sanitize` prints one name per `TEXT` on stdout and exits 0. When the reader of its
  output goes away early, as in `envname sanitize ... | head -1`, it stops quietly and
  exits 141, the status a shell gives a program stopped by a closed pipe. Any other
  write error, such as a full disk, is not hidden. Started without a stdout at all
  (`>&-`, `pythonw`), it prints nothing and exits 0.
- A usage error (an unknown option or rule set, a missing argument, an invalid
  `--prefix`) exits 2 with a usage message on stderr. A message longer than 300
  characters is cut at 300 and followed by its length, and an unknown `--rules` value is
  quoted like a name in an error: at most 60 characters, never past its first `=`.
- Started without a stderr (`2>&-`, `pythonw`), every command keeps the exit status
  above and prints no message, not even a usage line on stdout.
- When the reader of stderr goes away (`2>&1 | head -c 0`), `check` stops reporting,
  still checks every name and exits 1 or 0, and a usage error still exits 2. When the
  reader of stdout goes away, `--help` and `--version` still exit 0. The message is lost,
  not the status; any other write error on stderr during `check`, such as a full disk, is
  not hidden.
- Put `--` before a name that starts with `-`.

## Stability

From 1.0.0 envname follows Semantic Versioning. Stable: the five names in `__all__`,
their parameter names, keyword-only markers and defaults, what each rule set accepts,
the exception types, the `InvalidEnvName` attributes and their meaning, and the command
line with its exit codes. The wording of reasons and messages may be improved in a
minor release; match on the attributes, not on the text.

envname supports CPython 3.10 to 3.14, including the free-threaded build of 3.14, and
has no dependencies.

## Sources

Fetched on 2026-10-22 and checked in the test suite. Each one is pinned to a fixed
revision (a release, a commit or a versioned path), and `tests/upstream/MANIFEST.json`
records its URL, revision, size and sha256, so `python scripts/fetch_upstream.py` gets
the same bytes for everyone:

- POSIX.1-2024 XBD 3.216 Name and 6.1 Portable Character Set:
  https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap03.html and
  https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap06.html
- POSIX.1-2024 XBD 8.1 Environment Variable Definition:
  https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap08.html
- POSIX `setenv`: https://pubs.opengroup.org/onlinepubs/9799919799/functions/setenv.html
- The Bash Reference Manual, `doc/bashref.html` in the bash 5.3 release archive:
  https://ftp.gnu.org/gnu/bash/bash-5.3.tar.gz (the manual is also at
  https://www.gnu.org/software/bash/manual/bash.html)
- Windows environment variables, the source of the Microsoft Learn page
  (https://learn.microsoft.com/en-us/windows/win32/procthread/environment-variables) at
  commit 3aee48a of https://github.com/MicrosoftDocs/win32
- The Unicode Character Database, `UnicodeData.txt` for Unicode 13.0.0 to 16.0.0 (the
  versions of Python 3.10 to 3.14): https://www.unicode.org/Public/
- python-dotenv `parser.py` and compose-go `template/template.go`, at the commits in the
  manifest.

The suite also asks a real `bash`, the operating system call that stores a variable
(`SetEnvironmentVariableW` on Windows, `setenv` elsewhere), Python's `os.putenv` and,
when it is installed, python-dotenv.
