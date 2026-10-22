"""Command line: ``envname check`` and ``envname sanitize``."""

from __future__ import annotations

import argparse
import errno
import os
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, NoReturn

from ._rules import RULES, InvalidEnvName, _quote, _require_rules, check_env_name
from ._sanitize import sanitize_env_name

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

# 128 + SIGPIPE: the status a shell reports for a writer whose reader went away.
READER_GONE = 141
_LONGEST_ERROR = 300


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        if sys.stderr is None:
            # argparse would print the usage on stdout, where it would pass for a name.
            self.exit(2)
        # argparse repeats the offending argument, which can be as long as the OS allows.
        if len(message) > _LONGEST_ERROR:
            message = f"{message[:_LONGEST_ERROR]}... ({len(message)} characters)"
        super().error(message)

    def _print_message(self, message: str, file: SupportsWrite[str] | None = None) -> None:
        # Python 3.10 writes to a missing stream (pythonw, `2>&-`) and dies with
        # AttributeError, turning exit 2 or 0 into 1; 3.11+ skips the write, as here.
        file = file or sys.stderr
        if message and file is not None:
            try:
                file.write(message)
                _flush(file)
            except OSError:
                # The message is lost, not the status (2 for a usage error, 0 for --help).
                _to_null(file)


def _rules(value: str) -> str:
    try:
        return _require_rules(value)
    except ValueError:
        choices = ", ".join(map(repr, RULES))
        raise argparse.ArgumentTypeError(
            f"invalid choice: {_quote(value)} (choose from {choices})"
        ) from None


def _parser() -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    from . import __version__

    parser = _Parser(
        prog="envname", description="Validate and sanitize environment variable names."
    )
    parser.add_argument("--version", action="version", version=f"envname {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="exit 1 if any NAME is invalid")
    check.add_argument("names", nargs="+", metavar="NAME")
    check.add_argument("--rules", type=_rules, default="shell", metavar="{" + ",".join(RULES) + "}")
    sanitize = commands.add_parser("sanitize", help="print a valid name for each TEXT")
    sanitize.add_argument("texts", nargs="+", metavar="TEXT")
    sanitize.add_argument("--keep-case", action="store_true", help="do not upper-case")
    sanitize.add_argument("--prefix", default="", help="a valid name to put in front")
    return parser, sanitize


def _flush(stream: object) -> None:
    flush = getattr(stream, "flush", None)
    if flush is not None:
        flush()


def _reader_gone(exc: OSError) -> bool:
    # Windows reports a pipe whose reader has gone (`| head -1`) as EINVAL.
    windows = sys.platform == "win32"
    return isinstance(exc, BrokenPipeError) or (windows and exc.errno == errno.EINVAL)


def _to_null(stream: object) -> None:
    # The unwritten text stays buffered; on the null device the flush at exit cannot fail
    # again and turn the exit status into 120.
    try:
        target = stream.fileno()  # type: ignore[attr-defined]
    except (AttributeError, OSError, ValueError):
        return
    null = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null, target)
    finally:
        os.close(null)


def _warn(message: str) -> bool:
    """Write one line on stderr; return False once nobody can read it."""
    # A name can hold characters the console encoding cannot show (cp1252 on Windows);
    # escaping them beats crashing halfway through the report.
    stream = sys.stderr
    if stream is None:
        # Started without a stderr (pythonw, `2>&-`): the exit status still reports it.
        return False
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        stream.write(message.encode(encoding, "backslashreplace").decode(encoding) + "\n")
        stream.flush()
    except OSError as exc:
        if not _reader_gone(exc):
            raise
        _to_null(stream)
        return False
    return True


def _print_lines(lines: list[str]) -> int:
    if sys.stdout is None:
        # Started without a stdout at all (pythonw, `>&-`): print() would drop the lines too.
        return 0
    try:
        for line in lines:
            print(line)
        sys.stdout.flush()
    except OSError as exc:
        if not _reader_gone(exc):
            raise
        _to_null(sys.stdout)
        return READER_GONE
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit status."""
    parser, sanitize = _parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        failed = False
        report = True
        for name in args.names:
            try:
                check_env_name(name, rules=args.rules)
            except InvalidEnvName as exc:
                failed = True
                if report:
                    report = _warn(f"envname: {exc}")
        return 1 if failed else 0
    upper = not args.keep_case
    try:
        lines = [sanitize_env_name(text, upper=upper, prefix=args.prefix) for text in args.texts]
    except InvalidEnvName as exc:
        sanitize.error(f"--prefix: {exc}")
    return _print_lines(lines)
