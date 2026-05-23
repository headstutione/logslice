"""Query DSL for filtering log entries using field-based expressions."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class QueryCondition:
    """A single condition: field operator value."""
    field: str
    operator: str  # eq, neq, contains, regex, gt, lt
    value: str

    _OPERATORS = {"eq", "neq", "contains", "regex", "gt", "lt"}

    def __post_init__(self):
        if self.operator not in self._OPERATORS:
            raise ValueError(f"Unknown operator '{self.operator}'. Valid: {self._OPERATORS}")

    def matches(self, entry: LogEntry) -> bool:
        """Evaluate this condition against a log entry."""
        # Resolve value from entry fields or groups
        actual = None
        if self.field == "message":
            actual = entry.message
        elif self.field == "raw":
            actual = entry.raw
        elif entry.groups and self.field in entry.groups:
            actual = entry.groups[self.field]
        else:
            return False

        if self.operator == "eq":
            return actual == self.value
        elif self.operator == "neq":
            return actual != self.value
        elif self.operator == "contains":
            return self.value in actual
        elif self.operator == "regex":
            return bool(re.search(self.value, actual))
        elif self.operator == "gt":
            try:
                return float(actual) > float(self.value)
            except (ValueError, TypeError):
                return False
        elif self.operator == "lt":
            try:
                return float(actual) < float(self.value)
            except (ValueError, TypeError):
                return False
        return False


@dataclass
class Query:
    """A query composed of multiple conditions joined by AND logic."""
    conditions: List[QueryCondition] = field(default_factory=list)
    limit: Optional[int] = None

    def matches(self, entry: LogEntry) -> bool:
        return all(c.matches(entry) for c in self.conditions)

    def apply(self, entries: List[LogEntry]) -> List[LogEntry]:
        results = [e for e in entries if self.matches(e)]
        if self.limit is not None:
            results = results[:self.limit]
        return results
