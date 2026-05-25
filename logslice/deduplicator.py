"""Deduplication support for log entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import md5
from typing import Iterable, Iterator, Optional

from logslice.parser import LogEntry


@dataclass
class DeduplicatorConfig:
    """Configuration for log entry deduplication."""

    # Fields whose values form the dedup key; empty means use raw line
    key_fields: list[str] = field(default_factory=list)
    # Maximum number of unique keys to track (0 = unlimited)
    max_seen: int = 0
    # If True, emit only the *first* occurrence; otherwise drop duplicates silently
    keep_first: bool = True

    def __post_init__(self) -> None:
        if self.max_seen < 0:
            raise ValueError("max_seen must be >= 0")


class Deduplicator:
    """Filters duplicate LogEntry objects based on a configurable key."""

    def __init__(self, config: Optional[DeduplicatorConfig] = None) -> None:
        self._config = config or DeduplicatorConfig()
        self._seen: dict[str, int] = {}  # key -> occurrence count

    @property
    def config(self) -> DeduplicatorConfig:
        return self._config

    def _make_key(self, entry: LogEntry) -> str:
        """Derive a dedup key from the entry."""
        if not self._config.key_fields:
            return entry.raw
        parts = [
            str(entry.groups.get(f, "")) for f in self._config.key_fields
        ]
        return md5("|".join(parts).encode()).hexdigest()

    def is_duplicate(self, entry: LogEntry) -> bool:
        """Return True if *entry* has been seen before."""
        key = self._make_key(entry)
        seen_count = self._seen.get(key, 0)
        if seen_count == 0:
            # First time — check capacity
            if self._config.max_seen and len(self._seen) >= self._config.max_seen:
                # Table full; treat as duplicate to avoid unbounded growth
                return True
            self._seen[key] = 1
            return False
        self._seen[key] = seen_count + 1
        return True

    def filter(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield only unique entries according to the configured key."""
        for entry in entries:
            if not self.is_duplicate(entry):
                yield entry

    def seen_count(self, entry: LogEntry) -> int:
        """Return how many times *entry*'s key has been observed."""
        return self._seen.get(self._make_key(entry), 0)

    def reset(self) -> None:
        """Clear the internal seen-key table."""
        self._seen.clear()
