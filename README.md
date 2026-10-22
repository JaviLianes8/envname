# envname

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Validate and sanitize environment variable names against POSIX, shell and OS rules.

A program that creates environment variables from user input, config keys or `.env`
files has to decide which names are valid. The answer depends on who reads the name: a
shell only expands `[A-Za-z_][A-Za-z0-9_]*`, the POSIX utilities use upper-case names
only, and the operating system stores almost anything. `envname` names those three rule
sets, tells you why a name fails and where, and turns arbitrary text into a safe name.

## Install

```
pip install envname
```

Python 3.10 or newer, no dependencies.

## Usage

### Validate

```python
from envname import is_valid_env_name

print(is_valid_env_name("PATH"))  # True
print(is_valid_env_name("1ST_VALUE"))  # False
print(is_valid_env_name("MY-VAR"))  # False
print(is_valid_env_name("KEY=VALUE"))  # False
print(is_valid_env_name("path", rules="portable"))  # False
print(is_valid_env_name("my-var", rules="environ"))  # True
```

### Explain what is wrong

`check_env_name` returns the name when it is valid and raises `InvalidEnvName`, a
`ValueError`, when it is not. The error carries `name`, `rules`, a human `reason` and
the `index` of the first offending character (None for an empty name).

```python
from envname import InvalidEnvName, check_env_name

try:
    check_env_name("MY-VAR")
except InvalidEnvName as exc:
    print(exc)  # invalid shell environment variable name 'MY-VAR': '-' is not allowed at index 2
    print(exc.index)  # 2

print(check_env_name("DATABASE_URL", rules="portable"))  # DATABASE_URL
```

### Sanitize

`sanitize_env_name` turns any text into a valid name. Accented letters, ligatures and
full-width forms are folded to ASCII, every other run of characters outside
`[A-Za-z0-9_]` becomes one underscore, an optional `prefix` (itself a valid name) goes
in front, an underscore is added when the result would be empty or start with a digit,
and the name is upper-cased unless `upper=False`. The result is always a valid `shell`
name, and a valid `portable` one when upper-cased.

```python
from envname import sanitize_env_name

print(sanitize_env_name("my  var!!"))  # MY_VAR_
print(sanitize_env_name("1st-value"))  # _1ST_VALUE
print(sanitize_env_name("Crème brûlée"))  # CREME_BRULEE
print(sanitize_env_name("db.host", prefix="APP_"))  # APP_DB_HOST
print(sanitize_env_name("host.name", upper=False))  # host_name
```

Letters with no ASCII decomposition, such as `ß` or `ø`, still become an underscore.

### Names that already exist

The environment can hold names no shell could type. Check names you read back with
`rules="environ"`, and names you create with `shell` or `portable`:

```python
from envname import is_valid_env_name

env = {"PATH": "/usr/bin", "ProgramFiles(x86)": "C:/Program Files (x86)", "my-var": "1"}
print([name for name in env if not is_valid_env_name(name)])  # ['ProgramFiles(x86)', 'my-var']
print(all(is_valid_env_name(name, rules="environ") for name in env))  # True
```

### Command line

`envname check` exits with status 1 when any name is invalid and explains each one on
stderr; `envname sanitize` prints one name per argument. Put `--` before a name that
starts with `-`.

```console
$ envname check PATH my-var
envname: invalid shell environment variable name 'my-var': '-' is not allowed at index 2
$ envname check --rules environ my-var
$ envname sanitize --prefix APP_ db.host "max connections"
APP_DB_HOST
APP_MAX_CONNECTIONS
```

`python -m envname` works the same way.

## Rules

| `rules` | A valid name | Source | Use it for |
| --- | --- | --- | --- |
| `"shell"` (default) | `[A-Za-z_][A-Za-z0-9_]*` | POSIX XBD 3.216 "Name", the Bash manual | names you export from a shell, reference as `$NAME` or `${NAME}`, or interpolate in Compose files |
| `"portable"` | `[A-Z_][A-Z0-9_]*` | POSIX XBD 8.1, the names the standard utilities use | names that follow the upper-case convention of the POSIX utilities, which most deployment tooling copies |
| `"environ"` | not empty, no `=`, no NUL | the C-level rules of POSIX `setenv` and the Windows environment documentation | names you read back from `os.environ` or pass through to a child process |

`portable` names are `shell` names, and `shell` names are `environ` names. Names are
matched case-sensitively and only ASCII letters count, as in the C locale.

Things worth knowing:

- POSIX keeps names with lower-case letters for applications, so they never clash with
  a variable a standard utility reads; upper-case `portable` names follow the
  utilities' own convention. POSIX advises against a leading digit in either case.
- Windows matches names case-insensitively, and Python's `os.environ` upper-cases keys
  there. Windows uses its own case table, which disagrees with Python's `str.upper` for
  letters such as `ß`, `ı` and `ﬁ`, so `envname` does not try to fold case for you:
  stick to `portable` names when they must work on Windows too.
- Windows allows a leading `=` for the hidden per-drive variables such as `=C:`, while
  its documentation says names cannot contain `=`. `environ` follows the documentation.
- `environ` checks the string, not its encoding. On POSIX, Python encodes names with
  `os.fsencode`, so a lone surrogate outside U+DC80 to U+DCFF passes the rule but
  cannot be set there; Windows accepts it.
- The Windows documentation gives 32,767 characters as the largest size of a variable.
  Python's `os.putenv` on Windows refuses a `name=value` string longer than that, so
  name and value together can hold 32,766 characters, while `SetEnvironmentVariableW`
  itself stores longer names. A name on its own cannot know its value, so no rule limits
  length.
- `.env` parsers are looser than shells: python-dotenv takes any unquoted key without
  `=`, `#` or whitespace. Such keys load, but a shell cannot read them, and Compose only
  interpolates `$NAME` when the name matches `[_a-z][_a-z0-9]*` ignoring case, which for
  ASCII names is exactly the `shell` rule set.

## Why

The usual shortcuts each answer a different question:

- `str.isidentifier()` checks Python identifiers, so it accepts `été` and `ﬁle`, which no
  shell in the C locale accepts as a name.
- `string.Template` uses `(?a:[_a-z][_a-z0-9]*)` with `re.IGNORECASE` to find
  placeholders in a template. It is the `shell` rule, but it finds names in text: it does
  not validate one, explain a failure, or know the other two rule sets.
- `os.environ` and `os.putenv` refuse only what the operating system refuses (an empty
  name, `=`, NUL), so `my-var` is stored without complaint and no shell can read it back.
- python-dotenv takes any unquoted key without `=`, `#` or whitespace.
- A hand-written regular expression is easy to get subtly wrong: forgetting the
  leading-digit rule, letting `=` through, accepting an empty string, or rejecting a real
  name such as `ProgramFiles(x86)` that it should only refuse to create.

`envname` is small, typed and has no dependencies. Its rules are tested against the
POSIX and Bash texts themselves, a real `bash`, the real call that stores a variable on
the operating system, Python's `os.putenv`, and the Unicode Character Database for the
sanitizer.

## Documentation

The [guide](https://github.com/JaviLianes8/envname/blob/main/GUIDE.md) is the full
reference: every function, its errors, the command line and the stability promise. The
[changelog](https://github.com/JaviLianes8/envname/blob/main/CHANGELOG.md) lists what
changed in each release.

## Development

`python scripts/fetch_upstream.py` downloads the specifications, the Unicode data and the
upstream sources listed in `tests/upstream/MANIFEST.json` (they are not part of the
repository; their tests skip without them). `scripts/check.ps1` runs format, lint, types
and tests. Set `ENVNAME_E2E=1` to also build the wheel and test the installed package.

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/envname/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
