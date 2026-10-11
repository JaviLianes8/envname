from envname import is_valid_env_name, sanitize_env_name


def test_accepts_plain_name() -> None:
    assert is_valid_env_name("PATH")


def test_accepts_leading_underscore_and_digits_after_start() -> None:
    assert is_valid_env_name("_my_var2")


def test_rejects_leading_digit() -> None:
    assert not is_valid_env_name("1PATH")


def test_rejects_invalid_characters() -> None:
    assert not is_valid_env_name("MY-VAR")
    assert not is_valid_env_name("my var")


def test_rejects_empty() -> None:
    assert not is_valid_env_name("")


def test_rejects_name_with_equals() -> None:
    assert not is_valid_env_name("KEY=VALUE")


def test_is_case_sensitive() -> None:
    assert is_valid_env_name("Path")
    assert is_valid_env_name("path")


def test_sanitize_collapses_invalid_runs_to_single_underscore() -> None:
    assert sanitize_env_name("my  var!!name") == "MY_VAR_NAME"


def test_sanitize_prefixes_underscore_when_starting_with_digit() -> None:
    assert sanitize_env_name("1st-value") == "_1ST_VALUE"


def test_sanitize_keeps_case_when_upper_is_false() -> None:
    assert sanitize_env_name("My-Var", upper=False) == "My_Var"


def test_sanitize_upper_is_the_default() -> None:
    assert sanitize_env_name("host.name") == "HOST_NAME"


def test_sanitize_empty_yields_a_valid_name() -> None:
    assert sanitize_env_name("") == "_"


def test_sanitize_all_invalid_yields_single_underscore() -> None:
    assert sanitize_env_name("@#$") == "_"


def test_sanitize_output_is_always_valid() -> None:
    for raw in ["", "1", "a b", "=", "---", "Ünïcødé", "9lives"]:
        assert is_valid_env_name(sanitize_env_name(raw))
