"""Tests for logslice.parser module."""

import pytest
from logslice.parser import LogEntry, LogParser, ParseConfig


SAMPLE_LINES = [
    "2024-01-10 ERROR Something went wrong\n",
    "2024-01-10 INFO  Service started\n",
    "2024-01-10 DEBUG Verbose detail\n",
    "2024-01-10 ERROR Another failure\n",
    "2024-01-10 WARN  Low disk space\n",
]


def _parse(lines, **kwargs):
    cfg = ParseConfig(**kwargs)
    parser = LogParser(cfg)
    return list(parser.parse_lines(iter(lines)))


def test_no_filter_returns_all_lines():
    entries = _parse(SAMPLE_LINES)
    assert len(entries) == 5


def test_include_filter():
    entries = _parse(SAMPLE_LINES, include="ERROR")
    assert len(entries) == 2
    assert all("ERROR" in e.raw for e in entries)


def test_exclude_filter():
    entries = _parse(SAMPLE_LINES, exclude="DEBUG")
    assert len(entries) == 4
    assert all("DEBUG" not in e.raw for e in entries)


def test_include_and_exclude_combined():
    entries = _parse(SAMPLE_LINES, include="ERROR|WARN", exclude="Another")
    assert len(entries) == 2


def test_pattern_with_named_groups():
    pattern = r"(?P<level>ERROR|INFO|DEBUG|WARN)\s+(?P<msg>.+)"
    entries = _parse(SAMPLE_LINES, pattern=pattern)
    assert len(entries) == 5
    assert entries[0].groups["level"] == "ERROR"
    assert "Something went wrong" in entries[0].groups["msg"]


def test_pattern_no_match_excludes_line():
    entries = _parse(SAMPLE_LINES, pattern=r"CRITICAL")
    assert entries == []


def test_ignore_case():
    entries = _parse(SAMPLE_LINES, include="error", ignore_case=True)
    assert len(entries) == 2


def test_line_numbers_are_correct():
    entries = _parse(SAMPLE_LINES)
    for i, entry in enumerate(entries, start=1):
        assert entry.line_number == i


def test_log_entry_str():
    entry = LogEntry(line_number=1, raw="hello\n")
    assert str(entry) == "hello"
