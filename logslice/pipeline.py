"""Pipeline: orchestrates parsing, querying, formatting, and optional aggregation."""
from dataclasses import dataclass, field
from typing import List, Optional, Iterator

from logslice.parser import LogParser, ParseConfig, LogEntry
from logslice.query import Query
from logslice.formatter import Formatter
from logslice.aggregator import Aggregator, AggregationConfig, AggregationResult
from logslice.report import ReportRenderer


@dataclass
class PipelineConfig:
    parse: ParseConfig = field(default_factory=ParseConfig)
    query: Optional[Query] = None
    template: str = "{raw}"
    aggregate: Optional[AggregationConfig] = None
    limit: Optional[int] = None


class Pipeline:
    """Runs the full logslice processing pipeline."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._parser = LogParser(config.parse)
        self._formatter = Formatter(config.template)
        self._aggregator = (
            Aggregator(config.aggregate) if config.aggregate else None
        )
        self._reporter = ReportRenderer()

    def process(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield formatted output lines, applying query and limit."""
        count = 0
        for entry in self._parser.parse(lines):
            if self.config.query and not self.config.query.matches(entry):
                continue
            if self.config.limit is not None and count >= self.config.limit:
                break
            yield self._formatter.format_entry(entry)
            count += 1

    def process_to_list(self, lines: Iterator[str]) -> List[str]:
        return list(self.process(lines))

    def aggregate_lines(
        self, lines: Iterator[str], output_format: str = "text"
    ) -> str:
        """Parse + filter + aggregate, return rendered report string."""
        if not self._aggregator:
            raise ValueError("No AggregationConfig provided to pipeline.")
        entries: List[LogEntry] = []
        for entry in self._parser.parse(lines):
            if self.config.query and not self.config.query.matches(entry):
                continue
            entries.append(entry)

        result: AggregationResult = self._aggregator.aggregate(entries)
        if output_format == "csv":
            return self._reporter.render_csv(result)
        return self._reporter.render_text(result)

    def summary(self) -> dict:
        """Return pipeline configuration summary."""
        return {
            "template": self.config.template,
            "limit": self.config.limit,
            "has_query": self.config.query is not None,
            "has_aggregation": self._aggregator is not None,
        }
