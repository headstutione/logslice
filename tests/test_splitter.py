"""Tests for logslice.splitter."""

import pytest

from logslice.parser import LogEntry
from logslice.splitter import SplitRule, Splitter, SplitterConfig


def make_entry(raw: str, **groups: str) -> LogEntry:
    return LogEntry(raw=raw, groups=dict(groups))


# ---------------------------------------------------------------------------
# SplitRule
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid pattern"):
        SplitRule(name="bad", pattern="[unclosed")


def test_rule_matches_raw_line():
    rule = SplitRule(name="errors", pattern=r"ERROR")
    assert rule.matches(make_entry("2024-01-01 ERROR something broke"))


def test_rule_no_match_raw_line():
    rule = SplitRule(name="errors", pattern=r"ERROR")
    assert not rule.matches(make_entry("2024-01-01 INFO all good"))


def test_rule_matches_named_field():
    rule = SplitRule(name="warns", pattern=r"WARN", field="level")
    entry = make_entry("raw line", level="WARN")
    assert rule.matches(entry)


def test_rule_field_missing_falls_back_to_raw():
    rule = SplitRule(name="errors", pattern=r"ERROR", field="level")
    entry = make_entry("ERROR in raw")  # no 'level' group
    assert rule.matches(entry)


# ---------------------------------------------------------------------------
# Splitter — basic partitioning
# ---------------------------------------------------------------------------

def _make_splitter(multi_match: bool = False) -> Splitter:
    config = SplitterConfig(
        rules=[
            SplitRule(name="errors", pattern=r"ERROR"),
            SplitRule(name="warnings", pattern=r"WARN"),
        ],
        default_bucket="info",
        multi_match=multi_match,
    )
    return Splitter(config)


def test_split_routes_to_correct_buckets():
    splitter = _make_splitter()
    entries = [
        make_entry("ERROR something"),
        make_entry("WARN low disk"),
        make_entry("INFO all fine"),
    ]
    result = splitter.split(entries)
    assert len(result["errors"]) == 1
    assert len(result["warnings"]) == 1
    assert len(result["info"]) == 1


def test_split_default_bucket_receives_unmatched():
    splitter = _make_splitter()
    entries = [make_entry("DEBUG verbose"), make_entry("TRACE even more")]
    result = splitter.split(entries)
    assert len(result["info"]) == 2


def test_split_single_match_mode_first_rule_wins():
    splitter = _make_splitter(multi_match=False)
    entry = make_entry("ERROR WARN both keywords")
    result = splitter.split([entry])
    assert len(result["errors"]) == 1
    assert len(result["warnings"]) == 0


def test_split_multi_match_places_entry_in_multiple_buckets():
    splitter = _make_splitter(multi_match=True)
    entry = make_entry("ERROR WARN both keywords")
    result = splitter.split([entry])
    assert len(result["errors"]) == 1
    assert len(result["warnings"]) == 1
    # Should NOT also appear in default bucket
    assert len(result["info"]) == 0


def test_split_empty_input_returns_empty_buckets():
    splitter = _make_splitter()
    result = splitter.split([])
    assert result["errors"] == []
    assert result["warnings"] == []
    assert result["info"] == []


def test_splitter_exposes_config():
    config = SplitterConfig(rules=[], default_bucket="rest")
    splitter = Splitter(config)
    assert splitter.config is config
