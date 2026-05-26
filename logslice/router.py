"""Route log entries to different outputs based on matching rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class RouteRule:
    """A single routing rule: if *pattern* matches, send entry to *destination*."""

    destination: str
    pattern: str
    field: Optional[str] = None  # None → match against raw line

    def __post_init__(self) -> None:
        try:
            self._re = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid pattern {self.pattern!r}: {exc}") from exc

    def matches(self, entry: LogEntry) -> bool:
        text = entry.groups.get(self.field, entry.raw) if self.field else entry.raw
        return bool(self._re.search(text))


@dataclass
class RouterConfig:
    rules: List[RouteRule] = field(default_factory=list)
    default_destination: str = "default"
    stop_on_first_match: bool = True


Sink = Callable[[LogEntry], None]


class Router:
    """Route entries to named sinks according to ordered rules."""

    def __init__(self, config: RouterConfig) -> None:
        self._config = config
        self._sinks: Dict[str, List[Sink]] = {}

    @property
    def config(self) -> RouterConfig:
        return self._config

    def register(self, destination: str, sink: Sink) -> None:
        """Attach a callable sink to a named destination."""
        self._sinks.setdefault(destination, []).append(sink)

    def route(self, entry: LogEntry) -> str:
        """Determine destination for *entry* and invoke registered sinks.

        Returns the destination name that was selected.
        """
        destination = self._config.default_destination

        for rule in self._config.rules:
            if rule.matches(entry):
                destination = rule.destination
                if self._config.stop_on_first_match:
                    break

        for sink in self._sinks.get(destination, []):
            sink(entry)

        return destination

    def route_many(self, entries) -> Dict[str, List[LogEntry]]:
        """Route an iterable of entries; return a mapping of destination → entries."""
        result: Dict[str, List[LogEntry]] = {}
        for entry in entries:
            dest = self.route(entry)
            result.setdefault(dest, []).append(entry)
        return result
