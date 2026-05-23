"""Command-line interface for logslice."""

import argparse
import sys
from typing import List, Optional

from logslice.formatter import Formatter
from logslice.parser import ParseConfig, LogParser
from logslice.query_parser import QueryParseError, parse_query


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log file parser and filter utility.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument("-p", "--pattern", default=None, help="Regex pattern to parse each log line")
    p.add_argument("-i", "--include", default=None, help="Include only lines matching this regex")
    p.add_argument("-e", "--exclude", default=None, help="Exclude lines matching this regex")
    p.add_argument("-q", "--query", default=None, help="Field query expression, e.g. 'message:contains:ERROR'")
    p.add_argument("-t", "--template", default=None, help="Output template, e.g. '{message}'")
    p.add_argument("-n", "--limit", type=int, default=None, help="Maximum number of output lines")
    return p


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # --- Input ---
    if args.file:
        try:
            source = open(args.file, encoding="utf-8")
        except OSError as exc:
            print(f"logslice: error opening file: {exc}", file=sys.stderr)
            return 1
    else:
        source = sys.stdin

    try:
        lines = source.read().splitlines()
    finally:
        if args.file:
            source.close()

    # --- Parse ---
    config = ParseConfig(
        pattern=args.pattern,
        include=args.include,
        exclude=args.exclude,
    )
    log_parser = LogParser(config)
    entries = log_parser.parse_lines(lines)

    # --- Query ---
    if args.query:
        try:
            query = parse_query(args.query)
            if args.limit and query.limit is None:
                query.limit = args.limit
            entries = query.apply(entries)
        except QueryParseError as exc:
            print(f"logslice: query error: {exc}", file=sys.stderr)
            return 1
    elif args.limit:
        entries = entries[: args.limit]

    # --- Format & Output ---
    formatter = Formatter(template=args.template)
    print(formatter.render(entries))
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
