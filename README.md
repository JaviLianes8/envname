# envname

Validate and sanitize environment variable names against POSIX, shell and OS rules.

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
| `"portable"` | `[A-Z_][A-Z0-9_]*` | POSIX XBD 8.1, the names the standard utilities use | names you publish for other people: settings, documentation, deployment manifests |
| `"environ"` | not empty, no `=`, no NUL | POSIX `setenv`, the Windows environment documentation | names you read back from `os.environ` or pass through to a child process |

`portable` names are `shell` names, and `shell` names are `environ` names. Names are
matched case-sensitively and only ASCII letters count, as in the C locale.

Things worth knowing:

- POSIX reserves names with lower-case letters for applications and advises against
  names that start with a digit anywhere, which is why `portable` exists.
- Windows matches names case-insensitively, and Python's `os.environ` upper-cases keys
  there. Windows uses its own case table, which disagrees with Python's `str.upper` for
  letters such as `ß`, `ı` and `ﬁ`, so `envname` does not try to fold case for you:
  stick to `portable` names when they must work on Windows too.
- Windows allows a leading `=` for the hidden per-drive variables such as `=C:`, while
  its documentation says names cannot contain `=`. `environ` follows the documentation.
- Windows limits a variable to 32,767 characters, name and value together; Python
  enforces that in `os.environ`. A name on its own cannot know its value, so no rule
  limits length.
- `.env` parsers are looser than shells: python-dotenv takes any unquoted key without `=`, `#`
  or whitespace. Such keys load, but a shell cannot read them and Compose only
  interpolates `$NAME` for `shell` names.

## Why

Most projects re-check environment variable names with a one-off regex that quietly
drifts: it forgets the leading-digit rule, lets a stray `=` through, accepts an empty
string, or rejects real names like `ProgramFiles(x86)` that it should only refuse to
create. `envname` names the three rule sets POSIX and the operating systems actually
define, explains why a name fails, and turns arbitrary text into a safe name. It is
typed, has no dependencies, and its rules are tested against a real `bash` and the
real operating system call that stores variables.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
