# envname

Validate and sanitize POSIX environment variable names

## Install

```
pip install envname
```

## Usage

```python
from envname import is_valid_env_name, sanitize_env_name

is_valid_env_name("PATH")        # True
is_valid_env_name("1ST_VALUE")   # False, starts with a digit
is_valid_env_name("MY-VAR")      # False, '-' is not allowed
is_valid_env_name("KEY=VALUE")   # False, '=' is not allowed
is_valid_env_name("")            # False, names are never empty

sanitize_env_name("my  var!!")   # "MY_VAR_"
sanitize_env_name("1st-value")   # "_1ST_VALUE"
sanitize_env_name("host.name", upper=False)  # "host_name"
```

A valid name matches `[A-Za-z_][A-Za-z0-9_]*`: it starts with a letter or an
underscore, holds only letters, digits and underscores, is never empty and carries
no `=`. Matching is case-sensitive. `sanitize_env_name` collapses each run of
disallowed characters to a single underscore, prefixes an underscore when the result
would start with a digit or be empty, and upper-cases unless `upper=False`.

## Why

Shells and POSIX agree on what an environment variable name may contain, yet most
projects re-check it with a one-off regex that quietly drifts: it forgets the
leading-digit rule, allows a stray `=`, or accepts an empty string. There is no small
typed primitive for this. `envname` gives you one function to validate and one to
coerce, both covered by tests, with no dependencies. Reach for it when you build env
names from user input, config keys or file names and need the result to be safe to
export.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
