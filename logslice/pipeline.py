"""Pipeline module for logslice.

Provides a high-level Pipeline class that wires together parsing,
querying, and formatting into a single reusable processing chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from .formatter import Formatter
from .parser import LogEntry, LogParser, ParseConfig
from .query import Query
from .query_parser import parse_query


@dataclass
class PipelineConfig:
    """Configuration for a processing pipeline.

    Attributes:
        parse_config: Configuration passed to the log parser.
        query_string: Optional DSL query string to filter entries.
        output_template: Optional format template for rendered output.
        limit: Maximum number of entries to emit (0 = unlimited).
    """

    parse_config: ParseConfig = field(default_factory=ParseConfig)
    query_string: str = ""
    output_template: Optional[str] = None
    limit: int = 0


class Pipeline:
    """End-to-end log processing pipeline.

    Combines a :class:`~logslice.parser.LogParser`, an optional
    :class:`~logslice.query.Query`, and a
    :class:`~logslice.formatter.Formatter` into a single object that
    accepts raw log lines and yields formatted strings.

    Example::

        cfg = PipelineConfig(
            query_string='level == "ERROR"',
            output_template="[{level}] {message}",
            limit=100,
        )
        pipeline = Pipeline(cfg)
        for line in pipeline.process(open("app.log")):
            print(line)
    """

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._parser = LogParser(config.parse_config)
        self._query: Query = parse_query(config.query_string)
        self._formatter = Formatter(
            template=config.output_template
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, lines: Iterable[str]) -> Iterator[str]:
        """Parse *lines*, apply query filters, and yield formatted output.

        Parameters
        ----------
        lines:
            Any iterable of raw log line strings (e.g. an open file
            object, a list, or a generator).

        Yields
        ------
        str
            One formatted string per matching log entry.
        """
        entries = self._parser.parse(lines)
        matched = self._apply_query(entries)
        count = 0
        for entry in matched:
            yield self._formatter.format_entry(entry)
            count += 1
            if self._config.limit and count >= self._config.limit:
                break

    def process_to_list(self, lines: Iterable[str]) -> List[str]:
        """Convenience wrapper that collects :meth:`process` into a list."""
        return list(self.process(lines))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_query(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield only entries that satisfy the current query."""
        for entry in entries:
            if self._query.matches(entry):
                yield entry
