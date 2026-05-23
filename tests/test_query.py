"""Tests for logslice.query — QueryCondition and Query."""

import pytest
from logslice.parser import LogEntry
from logslice.query import Query, QueryCondition


def make_entry(message="hello world", raw=None, groups=None):
    return LogEntry(
        raw=raw or message,
        message=message,
        groups=groups or {},
    )


# --- QueryCondition ---

def test_condition_eq_match():
    cond = QueryCondition(field="message", operator="eq", value="hello world")
    assert cond.matches(make_entry("hello world"))


def test_condition_eq_no_match():
    cond = QueryCondition(field="message", operator="eq", value="bye")
    assert not cond.matches(make_entry("hello world"))


def test_condition_contains():
    cond = QueryCondition(field="message", operator="contains", value="ERROR")
    assert cond.matches(make_entry("[ERROR] something broke"))


def test_condition_neq():
    cond = QueryCondition(field="message", operator="neq", value="ok")
    assert cond.matches(make_entry("fail"))


def test_condition_regex():
    cond = QueryCondition(field="message", operator="regex", value=r"\d{3}")
    assert cond.matches(make_entry("status 404 not found"))


def test_condition_gt_lt_on_group():
    entry = make_entry(groups={"status": "500"})
    assert QueryCondition(field="status", operator="gt", value="499").matches(entry)
    assert QueryCondition(field="status", operator="lt", value="501").matches(entry)


def test_condition_unknown_field_returns_false():
    cond = QueryCondition(field="nonexistent", operator="eq", value="x")
    assert not cond.matches(make_entry())


def test_invalid_operator_raises():
    with pytest.raises(ValueError, match="Unknown operator"):
        QueryCondition(field="message", operator="startswith", value="x")


# --- Query ---

def test_query_apply_all_match():
    entries = [make_entry("ERROR one"), make_entry("ERROR two"), make_entry("INFO ok")]
    q = Query(conditions=[QueryCondition("message", "contains", "ERROR")])
    result = q.apply(entries)
    assert len(result) == 2


def test_query_limit():
    entries = [make_entry(f"ERROR {i}") for i in range(10)]
    q = Query(conditions=[QueryCondition("message", "contains", "ERROR")], limit=3)
    assert len(q.apply(entries)) == 3


def test_empty_query_matches_all():
    entries = [make_entry("anything"), make_entry("else")]
    assert Query().apply(entries) == entries
