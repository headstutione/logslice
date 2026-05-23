"""Tests for logslice.aggregator module."""
import pytest
from logslice.parser import LogEntry
from logslice.aggregator import Aggregator, AggregationConfig, AggregationResult


def make_entry(raw: str, **groups) -> LogEntry:
    return LogEntry(raw=raw, groups=groups)


def test_aggregate_no_group_by_returns_total():
    entries = [make_entry("line1"), make_entry("line2"), make_entry("line3")]
    agg = Aggregator(AggregationConfig())
    result = agg.aggregate(entries)
    assert result.total == 3
    assert result.groups == {}


def test_aggregate_group_by_field():
    entries = [
        make_entry("a", level="ERROR"),
        make_entry("b", level="INFO"),
        make_entry("c", level="ERROR"),
        make_entry("d", level="DEBUG"),
    ]
    agg = Aggregator(AggregationConfig(group_by="level"))
    result = agg.aggregate(entries)
    assert result.total == 4
    assert result.groups["ERROR"] == 2
    assert result.groups["INFO"] == 1
    assert result.groups["DEBUG"] == 1


def test_aggregate_missing_field_falls_back_to_raw():
    entries = [
        make_entry("raw_line_1"),
        make_entry("raw_line_2"),
        make_entry("raw_line_1"),
    ]
    agg = Aggregator(AggregationConfig(group_by="level"))
    result = agg.aggregate(entries)
    assert result.groups.get("raw_line_1") == 2
    assert result.groups.get("raw_line_2") == 1


def test_top_n_returns_correct_count():
    entries = [
        make_entry("a", level="ERROR"),
        make_entry("b", level="ERROR"),
        make_entry("c", level="INFO"),
        make_entry("d", level="DEBUG"),
        make_entry("e", level="ERROR"),
    ]
    agg = Aggregator(AggregationConfig(group_by="level", top_n=2))
    result = agg.aggregate(entries)
    top = result.top(2)
    assert len(top) == 2
    assert top[0] == ("ERROR", 3)


def test_summary_includes_total_and_groups():
    entries = [make_entry("x", svc="web"), make_entry("y", svc="db")]
    agg = Aggregator(AggregationConfig(group_by="svc"))
    result = agg.aggregate(entries)
    summary = result.summary()
    assert summary["total"] == 2
    assert "groups" in summary
    assert summary["groups"]["web"] == 1


def test_aggregate_empty_entries_returns_zero_total():
    """Aggregating an empty list should return total=0 and no groups."""
    agg = Aggregator(AggregationConfig(group_by="level"))
    result = agg.aggregate([])
    assert result.total == 0
    assert result.groups == {}
