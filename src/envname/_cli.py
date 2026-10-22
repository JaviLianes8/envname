"""Command line: ``envname check`` and ``envname sanitize``."""

from __future__ import annotations

import argparse
import errno
import os
import sys
from collections.abc import Sequence
from typing import NoReturn

from ._rules import RULES, InvalidEnvName, _quote, _require_rules, check_env_name
from ._sanitize import sanitize_env_name

# 128 + SIGPIPE: the status a shell reports for a writer whose reader went away.
READER_GONE = 141
_LONGEST_ERROR = 300


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # argparse repeats the offending argument, which can be as long as the OS allows.
        if len(message) > _LONGEST_ERROR:
            message = f"{message[:_LONGEST_ERROR]}... ({len(message)} characters)"
        super().error(message)


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


def _warn(message: str) -> None:
    # A name can hold characters the console encoding cannot show (cp1252 on Windows);
    # escaping them beats crashing halfway through the report.
    stream = sys.stderr
    encoding = getattr(stream, "encoding", None) or "utf-8"
    stream.write(message.encode(encoding, "backslashreplace").decode(encoding) + "\n")


def _print_lines(lines: list[str]) -> int:
    try:
        for line in lines:
            print(line)
        sys.stdout.flush()
    except OSError as exc:
        # Windows reports a pipe whose reader has gone (`| head -1`) as EINVAL.
        windows = sys.platform == "win32"
        gone = isinstance(exc, BrokenPipeError) or (windows and exc.errno == errno.EINVAL)
        if not gone:
            raise
        # Point stdout at the null device so the flush at exit cannot fail again.
        try:
            target = sys.stdout.fileno()
        except (AttributeError, OSError, ValueError):
            return READER_GONE
        null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null, target)
        os.close(null)
        return READER_GONE
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit status."""
    parser, sanitize = _parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        failed = False
        for name in args.names:
            try:
                check_env_name(name, rules=args.rules)
            except InvalidEnvName as exc:
                _warn(f"envname: {exc}")
                failed = True
        return 1 if failed else 0
    upper = not args.keep_case
    try:
        lines = [sanitize_env_name(text, upper=upper, prefix=args.prefix) for text in args.texts]
    except InvalidEnvName as exc:
        sanitize.error(f"--prefix: {exc}")
    return _print_lines(lines)
