"""Validation and checking command-line interface."""

import argparse
import sys
from pathlib import Path
from typing import Never

from endpointcheck.config import ConfigurationError, load_configuration
from endpointcheck.reporting import format_report, safe_display
from endpointcheck.runner import run_checks


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        super().error(safe_display(message))


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="endpointcheck")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser(
        "validate", help="validate a JSON configuration without requests"
    )
    validate.add_argument("config_path", type=Path)
    check = commands.add_parser(
        "check", help="check configured endpoints and report health"
    )
    check.add_argument("config_path", type=Path)
    args = parser.parse_args(argv)
    try:
        settings = load_configuration(args.config_path)
    except ConfigurationError as error:
        print(f"error: {safe_display(str(error))}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(f"Configuration valid: {len(settings.endpoints)} endpoint(s).")
        return 0
    results = run_checks(settings)
    print(format_report(results))
    return 1 if any(result.outcome != "healthy" for result in results) else 0
