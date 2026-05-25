"""Tests for logslice.deduplicator."""

import pytest

from logslice.parser import LogEntry
from logslice.deduplicator import Deduplicator, DeduplicatorConfig


def make_entry(raw: str, groups: dict | None = None) -> LogEntry:
    return LogEntry(raw=raw, groups=groups or {})


# ---------------------------------------------------------------------------
# DeduplicatorConfig
# ---------------------------------------------------------------------------

def test_default_config_uses_raw_line():
    cfg = DeduplicatorConfig()
    assert cfg.key_fields == []
    assert cfg.max_seen == 0
    assert cfg.keep_first is True


def test_negative_max_seen_raises():
    with pytest.raises(ValueError, match="max_seen"):
        DeduplicatorConfig(max_seen=-1)


# ---------------------------------------------------------------------------
# Deduplicator — basic behaviour
# ---------------------------------------------------------------------------

def test_first_entry_is_not_duplicate():
    d = Deduplicator()
    entry = make_entry("INFO hello")
    assert d.is_duplicate(entry) is False


def test_second_identical_raw_is_duplicate():
    d = Deduplicator()
    entry = make_entry("INFO hello")
    d.is_duplicate(entry)
    assert d.is_duplicate(entry) is True


def test_different_raw_lines_not_duplicate():
    d = Deduplicator()
    assert d.is_duplicate(make_entry("line A")) is False
    assert d.is_duplicate(make_entry("line B")) is False


# ---------------------------------------------------------------------------
# filter()
# ---------------------------------------------------------------------------

def test_filter_removes_duplicates():
    d = Deduplicator()
    entries = [
        make_entry("alpha"),
        make_entry("beta"),
        make_entry("alpha"),
        make_entry("gamma"),
        make_entry("beta"),
    ]
    result = list(d.filter(entries))
    assert [e.raw for e in result] == ["alpha", "beta", "gamma"]


def test_filter_empty_input():
    d = Deduplicator()
    assert list(d.filter([])) == []


# ---------------------------------------------------------------------------
# key_fields
# ---------------------------------------------------------------------------

def test_key_fields_used_for_dedup():
    cfg = DeduplicatorConfig(key_fields=["level"])
    d = Deduplicator(cfg)
    e1 = make_entry("INFO msg1", {"level": "INFO"})
    e2 = make_entry("INFO msg2", {"level": "INFO"})  # same level -> duplicate
    e3 = make_entry("ERROR msg", {"level": "ERROR"})
    result = list(d.filter([e1, e2, e3]))
    assert len(result) == 2
    assert result[0].raw == "INFO msg1"
    assert result[1].raw == "ERROR msg"


def test_missing_key_field_treated_as_empty_string():
    cfg = DeduplicatorConfig(key_fields=["missing_field"])
    d = Deduplicator(cfg)
    e1 = make_entry("line1", {})
    e2 = make_entry("line2", {})  # same derived key -> duplicate
    result = list(d.filter([e1, e2]))
    assert len(result) == 1


# ---------------------------------------------------------------------------
# max_seen capacity
# ---------------------------------------------------------------------------

def test_max_seen_limits_table_size():
    cfg = DeduplicatorConfig(max_seen=2)
    d = Deduplicator(cfg)
    e1, e2, e3 = make_entry("a"), make_entry("b"), make_entry("c")
    assert d.is_duplicate(e1) is False
    assert d.is_duplicate(e2) is False
    # Table full — new unique key treated as duplicate
    assert d.is_duplicate(e3) is True


# ---------------------------------------------------------------------------
# seen_count & reset
# ---------------------------------------------------------------------------

def test_seen_count_increments():
    d = Deduplicator()
    entry = make_entry("repeated")
    d.is_duplicate(entry)
    d.is_duplicate(entry)
    d.is_duplicate(entry)
    assert d.seen_count(entry) == 3


def test_reset_clears_state():
    d = Deduplicator()
    entry = make_entry("x")
    d.is_duplicate(entry)
    d.reset()
    assert d.is_duplicate(entry) is False
