"""Log entry splitter: partitions a stream of entries into named buckets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from logslice.parser import LogEntry


@dataclass
class SplitRule:
    """A named rule that assigns matching entries to a bucket."""

    name: str
    pattern: str
    field: Optional[str] = None  # if None, match against raw line

    def __post_init__(self) -> None:
        try:
            self._regex = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid pattern for rule {self.name!r}: {exc}") from exc

    def matches(self, entry: LogEntry) -> bool:
        target = entry.groups.get(self.field, entry.raw) if self.field else entry.raw
        return bool(self._regex.search(target))


@dataclass
class SplitterConfig:
    """Configuration for the Splitter."""

    rules: List[SplitRule] = field(default_factory=list)
    default_bucket: str = "other"
    multi_match: bool = False  # if True, entry may appear in multiple buckets


class Splitter:
    """Partitions log entries into named buckets based on SplitRules."""

    def __init__(self, config: SplitterConfig) -> None:
        self._config = config

    @property
    def config(self) -> SplitterConfig:
        return self._config

    def split(self, entries: Iterable[LogEntry]) -> Dict[str, List[LogEntry]]:
        """Return a dict mapping bucket names to lists of matching entries."""
        buckets: Dict[str, List[LogEntry]] = {r.name: [] for r in self._config.rules}
        buckets[self._config.default_bucket] = []

        for entry in entries:
            placed = False
            for rule in self._config.rules:
                if rule.matches(entry):
                    buckets[rule.name].append(entry)
                    placed = True
                    if not self._config.multi_match:
                        break
            if not placed:
                buckets[self._config.default_bucket].append(entry)

        return buckets
