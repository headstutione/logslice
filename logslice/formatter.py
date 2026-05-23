"""Output formatters for log entries."""

from typing import List
from logslice.parser import LogEntry


DEFAULT_FORMAT = "{line_number}\t{raw}"


class Formatter:
    """Formats LogEntry objects for display or export."""

    def __init__(self, template: str = DEFAULT_FORMAT, show_line_numbers: bool = True):
        self.template = template
        self.show_line_numbers = show_line_numbers

    def format_entry(self, entry: LogEntry) -> str:
        """Format a single LogEntry using the configured template."""
        context = {
            "line_number": entry.line_number,
            "raw": entry.raw.rstrip("\n"),
            **entry.groups,
        }
        try:
            return self.template.format(**context)
        except KeyError as exc:
            raise ValueError(
                f"Template references unknown field {exc}. "
                f"Available fields: {list(context.keys())}"
            ) from exc

    def format_entries(self, entries: List[LogEntry]) -> List[str]:
        """Format a list of entries."""
        return [self.format_entry(e) for e in entries]

    def render(self, entries: List[LogEntry]) -> str:
        """Render all entries as a single newline-joined string."""
        return "\n".join(self.format_entries(entries))


class JsonFormatter:
    """Formats LogEntry objects as JSON lines."""

    def format_entry(self, entry: LogEntry) -> str:
        import json

        payload = {
            "line_number": entry.line_number,
            "raw": entry.raw.rstrip("\n"),
        }
        if entry.groups:
            payload["groups"] = entry.groups
        return json.dumps(payload)

    def render(self, entries: List[LogEntry]) -> str:
        return "\n".join(self.format_entry(e) for e in entries)
