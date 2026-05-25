"""Tests for logslice.query_parser — parse_query."""

import pytest
from logslice.parser import LogEntry
from logslice.query_parser import QueryParseError, parse_query


def make_entry(message="hello", groups=None):
    return LogEntry(raw=message, message=message, groups=groups or {})


def test_parse_single_condition():
    q = parse_query("message:contains:ERROR")
    assert len(q.conditions) == 1
    c = q.conditions[0]
    assert c.field == "message"
    assert c.operator == "contains"
    assert c.value == "ERROR"


def test_parse_multiple_conditions():
    q = parse_query("message:contains:ERROR AND level:eq:WARN")
    assert len(q.conditions) == 2


def test_parse_with_limit():
    q = parse_query("message:regex:timeout LIMIT 25")
    assert q.limit == 25
    assert len(q.conditions) == 1


def test_parse_empty_string_returns_empty_query():
    q = parse_query("")
    assert q.conditions == []
    assert q.limit is None


def test_parse_whitespace_only_returns_empty_query():
    q = parse_query("   ")
    assert q.conditions == []


def test_parse_invalid_operator_raises():
    with pytest.raises(QueryParseError, match="Unknown operator"):
        parse_query("message:startswith:ERR")


def test_parse_and_apply_integration():
    entries = [
        make_entry("ERROR: disk full"),
        make_entry("WARN: low memory"),
        make_entry("ERROR: timeout"),
    ]
    q = parse_query("message:contains:ERROR LIMIT 1")
    result = q.apply(entries)
    assert len(result) == 1
    assert "ERROR" in result[0].message


def test_parse_value_with_spaces():
    q = parse_query("message:contains:disk full")
    assert q.conditions[0].value == "disk full"


def test_parse_limit_zero_raises():
    """A LIMIT of zero is nonsensical and should raise QueryParseError."""
    with pytest.raises(QueryParseError, match="LIMIT"):
        parse_query("message:contains:ERROR LIMIT 0")


def test_parse_negative_limit_raises():
    """A negative LIMIT value should raise QueryParseError."""
    with pytest.raises(QueryParseError, match="LIMIT"):
        parse_query("message:contains:ERROR LIMIT -5")


def test_parse_non_integer_limit_raises():
    """A non-integer LIMIT value should raise QueryParseError."""
    with pytest.raises(QueryParseError, match="LIMIT"):
        parse_query("message:contains:ERROR LIMIT ten")
