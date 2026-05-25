"""Field transformation and normalization for log entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class TransformRule:
    """A single transformation rule applied to a named group field."""

    field: str
    transform: Callable[[str], str]
    label: Optional[str] = None

    def apply(self, entry: LogEntry) -> LogEntry:
        """Return a new LogEntry with the field transformed."""
        if entry.groups is None:
            return entry
        value = entry.groups.get(self.field)
        if value is None:
            return entry
        new_groups = dict(entry.groups)
        new_groups[self.field] = self.transform(value)
        return LogEntry(raw=entry.raw, groups=new_groups)


@dataclass
class TransformerConfig:
    """Configuration for the Transformer."""

    rules: List[TransformRule] = field(default_factory=list)
    stop_on_error: bool = False


class TransformError(Exception):
    """Raised when a transformation fails and stop_on_error is True."""


class Transformer:
    """Applies a sequence of TransformRules to LogEntry objects."""

    def __init__(self, config: TransformerConfig) -> None:
        self._config = config

    @property
    def config(self) -> TransformerConfig:
        return self._config

    def transform(self, entry: LogEntry) -> LogEntry:
        """Apply all rules to *entry* and return the (possibly new) entry."""
        for rule in self._config.rules:
            try:
                entry = rule.apply(entry)
            except Exception as exc:  # noqa: BLE001
                if self._config.stop_on_error:
                    label = rule.label or rule.field
                    raise TransformError(
                        f"Transform rule '{label}' failed: {exc}"
                    ) from exc
        return entry

    def transform_all(self, entries: List[LogEntry]) -> List[LogEntry]:
        """Transform a list of entries, returning a new list."""
        return [self.transform(e) for e in entries]


# ---------- built-in helpers ------------------------------------------------

def uppercase(value: str) -> str:
    return value.upper()


def lowercase(value: str) -> str:
    return value.lower()


def strip_whitespace(value: str) -> str:
    return value.strip()


def regex_replace(pattern: str, replacement: str) -> Callable[[str], str]:
    """Return a transform that replaces *pattern* with *replacement*."""
    compiled = re.compile(pattern)

    def _replace(value: str) -> str:
        return compiled.sub(replacement, value)

    return _replace
