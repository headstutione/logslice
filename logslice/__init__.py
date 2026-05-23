"""
logslice — Fast log file parser and filter utility.

Provides regex-based querying and flexible output formatting
for structured and unstructured log files.

Basic usage:
    from logslice import LogParser, ParseConfig, Formatter, parse_query

    config = ParseConfig(include_patterns=[r'ERROR|WARN'])
    parser = LogParser(config)
    entries = parser.parse_file('app.log')

    formatter = Formatter()
    print(formatter.render(entries))
"""

from logslice.parser import LogEntry, ParseConfig, LogParser
from logslice.formatter import Formatter
from logslice.query import Query, QueryCondition
from logslice.query_parser import parse_query, QueryParseError

__version__ = "0.1.0"
__author__ = "logslice contributors"
__all__ = [
    "LogEntry",
    "ParseConfig",
    "LogParser",
    "Formatter",
    "Query",
    "QueryCondition",
    "parse_query",
    "QueryParseError",
]
