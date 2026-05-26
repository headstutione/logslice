"""CLI helpers for configuring the Router from command-line arguments."""

from __future__ import annotations

import argparse
from typing import List

from logslice.router import RouteRule, RouterConfig


def add_router_args(parser: argparse.ArgumentParser) -> None:
    """Attach router-related flags to *parser*."""
    parser.add_argument(
        "--route",
        metavar="DEST:PATTERN",
        action="append",
        default=[],
        help=(
            "Route entries matching PATTERN to DEST. "
            "Use DEST:FIELD:PATTERN to match a named capture group. "
            "May be specified multiple times."
        ),
    )
    parser.add_argument(
        "--route-default",
        metavar="DEST",
        default="default",
        help="Destination name for entries that match no rule (default: 'default').",
    )
    parser.add_argument(
        "--route-all-matches",
        action="store_true",
        default=False,
        help="Continue matching rules after the first hit (default: stop on first match).",
    )


def _parse_single(spec: str) -> RouteRule:
    """Parse a single ``DEST:PATTERN`` or ``DEST:FIELD:PATTERN`` spec."""
    parts = spec.split(":", 2)
    if len(parts) == 2:
        destination, pattern = parts
        return RouteRule(destination=destination, pattern=pattern)
    if len(parts) == 3:
        destination, field, pattern = parts
        return RouteRule(destination=destination, pattern=pattern, field=field or None)
    raise argparse.ArgumentTypeError(
        f"Invalid --route spec {spec!r}. Expected DEST:PATTERN or DEST:FIELD:PATTERN."
    )


def build_router_config(args: argparse.Namespace) -> RouterConfig:
    """Construct a :class:`RouterConfig` from parsed *args*."""
    rules: List[RouteRule] = []
    for spec in getattr(args, "route", []) or []:
        rules.append(_parse_single(spec))

    return RouterConfig(
        rules=rules,
        default_destination=getattr(args, "route_default", "default"),
        stop_on_first_match=not getattr(args, "route_all_matches", False),
    )
