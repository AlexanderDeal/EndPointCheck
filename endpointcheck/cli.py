"""Minimal validation-only command-line interface."""

import argparse
import sys
from pathlib import Path

from endpointcheck.config import ConfigurationError, load_configuration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="endpointcheck")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser(
        "validate", help="validate a JSON configuration without requests"
    )
    validate.add_argument("config_path", type=Path)
    args = parser.parse_args(argv)
    try:
        settings = load_configuration(args.config_path)
    except ConfigurationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Configuration valid: {len(settings.endpoints)} endpoint(s).")
    return 0
