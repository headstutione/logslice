"""Aggregation utilities for summarizing log entries."""
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from logslice.parser import LogEntry


@dataclass
class AggregationConfig:
    group_by: Optional[str] = None  # field name to group by
    count: bool = True
    top_n: Optional[int] = None


@dataclass
class AggregationResult:
    total: int = 0
    groups: Dict[str, int] = field(default_factory=dict)
    config: AggregationConfig = field(default_factory=AggregationConfig)

    def top(self, n: int) -> List[tuple]:
        """Return top N groups by count."""
        return sorted(self.groups.items(), key=lambda x: x[1], reverse=True)[:n]

    def summary(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"total": self.total}
        if self.groups:
            top_n = self.config.top_n
            items = self.top(top_n) if top_n else sorted(
                self.groups.items(), key=lambda x: x[1], reverse=True
            )
            result["groups"] = dict(items)
        return result


class Aggregator:
    """Aggregates a list of LogEntry objects based on an AggregationConfig."""

    def __init__(self, config: AggregationConfig):
        self.config = config

    def aggregate(self, entries: List[LogEntry]) -> AggregationResult:
        result = AggregationResult(total=len(entries), config=self.config)
        if not self.config.group_by:
            return result

        key = self.config.group_by
        counter: Counter = Counter()
        for entry in entries:
            value = entry.groups.get(key) or entry.raw
            counter[value] += 1

        result.groups = dict(counter)
        return result
