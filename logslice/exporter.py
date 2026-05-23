"""Export pipeline results to various output formats (JSON, CSV, plain text)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class ExportConfig:
    format: str = "text"          # "text" | "json" | "csv"
    fields: List[str] = field(default_factory=list)  # empty = all fields
    delimiter: str = ","          # used for csv
    pretty_json: bool = False


class ExportError(Exception):
    """Raised when an export operation fails."""


class Exporter:
    """Serialises a list of LogEntry objects to the requested format."""

    def __init__(self, config: Optional[ExportConfig] = None) -> None:
        self.config = config or ExportConfig()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def export(self, entries: List[LogEntry]) -> str:
        fmt = self.config.format.lower()
        if fmt == "json":
            return self._to_json(entries)
        if fmt == "csv":
            return self._to_csv(entries)
        if fmt == "text":
            return self._to_text(entries)
        raise ExportError(f"Unknown export format: {fmt!r}")

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _entry_dict(self, entry: LogEntry) -> dict:
        data = {"raw": entry.raw, **entry.groups}
        if self.config.fields:
            return {k: data[k] for k in self.config.fields if k in data}
        return data

    def _to_json(self, entries: List[LogEntry]) -> str:
        rows = [self._entry_dict(e) for e in entries]
        indent = 2 if self.config.pretty_json else None
        return json.dumps(rows, indent=indent)

    def _to_csv(self, entries: List[LogEntry]) -> str:
        if not entries:
            return ""
        rows = [self._entry_dict(e) for e in entries]
        headers = list(rows[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=headers,
            delimiter=self.config.delimiter,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    def _to_text(self, entries: List[LogEntry]) -> str:
        return "\n".join(e.raw for e in entries)
