"""Core log file parser with regex-based filtering."""

import re
from dataclasses import dataclass, field
from typing import Iterator, List, Optional


@dataclass
class LogEntry:
    """Represents a single parsed log entry."""

    line_number: int
    raw: str
    groups: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.raw.rstrip("\n")


@dataclass
class ParseConfig:
    """Configuration for the log parser."""

    pattern: Optional[str] = None
    include: Optional[str] = None
    exclude: Optional[str] = None
    ignore_case: bool = False


class LogParser:
    """Parses and filters log files using regex patterns."""

    def __init__(self, config: ParseConfig):
        self.config = config
        flags = re.IGNORECASE if config.ignore_case else 0

        self._pattern = re.compile(config.pattern, flags) if config.pattern else None
        self._include = re.compile(config.include, flags) if config.include else None
        self._exclude = re.compile(config.exclude, flags) if config.exclude else None

    def parse_lines(self, lines: Iterator[str]) -> Iterator[LogEntry]:
        """Yield LogEntry objects for each matching line."""
        for line_number, raw in enumerate(lines, start=1):
            entry = self._try_match(line_number, raw)
            if entry is not None:
                yield entry

    def parse_file(self, filepath: str) -> Iterator[LogEntry]:
        """Open a file and yield matching LogEntry objects."""
        with open(filepath, "r", errors="replace") as fh:
            yield from self.parse_lines(fh)

    def _try_match(self, line_number: int, raw: str) -> Optional[LogEntry]:
        groups: dict = {}

        if self._pattern:
            m = self._pattern.search(raw)
            if not m:
                return None
            groups = m.groupdict()

        if self._include and not self._include.search(raw):
            return None

        if self._exclude and self._exclude.search(raw):
            return None

        return LogEntry(line_number=line_number, raw=raw, groups=groups)

    def collect(self, filepath: str) -> List[LogEntry]:
        """Return all matching entries as a list."""
        return list(self.parse_file(filepath))
