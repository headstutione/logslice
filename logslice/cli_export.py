"""CLI helpers for the --export flag added to logslice's main pipeline."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.exporter import Exporter, ExportConfig
from logslice.parser import LogEntry


def add_export_args(parser: argparse.ArgumentParser) -> None:
    """Attach export-related arguments to an existing ArgumentParser."""
    grp = parser.add_argument_group("export")
    grp.add_argument(
        "--export-format",
        dest="export_format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format for exported entries (default: text).",
    )
    grp.add_argument(
        "--export-fields",
        dest="export_fields",
        metavar="FIELD",
        nargs="+",
        default=[],
        help="Restrict exported fields (applies to json/csv).",
    )
    grp.add_argument(
        "--csv-delimiter",
        dest="csv_delimiter",
        default=",",
        metavar="CHAR",
        help="Column delimiter for CSV export (default: ',').",
    )
    grp.add_argument(
        "--pretty-json",
        dest="pretty_json",
        action="store_true",
        default=False,
        help="Pretty-print JSON output.",
    )


def build_export_config(args: argparse.Namespace) -> ExportConfig:
    """Construct an ExportConfig from parsed CLI arguments."""
    return ExportConfig(
        format=args.export_format,
        fields=args.export_fields or [],
        delimiter=args.csv_delimiter,
        pretty_json=args.pretty_json,
    )


def write_export(
    entries: List[LogEntry],
    config: ExportConfig,
    output=None,
) -> None:
    """Export *entries* using *config* and write the result to *output*.

    Parameters
    ----------
    entries:
        Filtered/processed log entries.
    config:
        Export configuration built from CLI args.
    output:
        File-like object to write to; defaults to ``sys.stdout``.
    """
    if output is None:
        output = sys.stdout
    result = Exporter(config).export(entries)
    if result:
        output.write(result)
        if not result.endswith("\n"):
            output.write("\n")
