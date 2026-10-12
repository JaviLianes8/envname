"""Command line: ``envname check`` and ``envname sanitize``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ._rules import RULES, InvalidEnvName, check_env_name
from ._sanitize import sanitize_env_name


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envname", description="Validate and sanitize environment variable names."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="exit 1 if any NAME is invalid")
    check.add_argument("names", nargs="+", metavar="NAME")
    check.add_argument("--rules", choices=RULES, default="shell")
    sanitize = commands.add_parser("sanitize", help="print a valid name for each TEXT")
    sanitize.add_argument("texts", nargs="+", metavar="TEXT")
    sanitize.add_argument("--keep-case", action="store_true", help="do not upper-case")
    sanitize.add_argument("--prefix", default="", help="a valid name to put in front")
    return parser


def _warn(message: str) -> None:
    # A name can hold characters the console encoding cannot show (cp1252 on Windows);
    # escaping them beats crashing halfway through the report.
    stream = sys.stderr
    encoding = getattr(stream, "encoding", None) or "utf-8"
    stream.write(message.encode(encoding, "backslashreplace").decode(encoding) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit status."""
    parser = _parser()
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
    try:
        for text in args.texts:
            print(sanitize_env_name(text, upper=not args.keep_case, prefix=args.prefix))
    except InvalidEnvName as exc:
        parser.error(f"--prefix: {exc}")
    return 0
