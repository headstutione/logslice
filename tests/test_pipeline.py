"""Tests for the Pipeline and PipelineConfig classes."""

import pytest
from logslice.pipeline import Pipeline, PipelineConfig
from logslice.parser import LogEntry, ParseConfig
from logslice.query import Query, QueryCondition


def make_entry(raw, groups=None):
    """Helper to create a LogEntry for testing."""
    return LogEntry(raw=raw, groups=groups or {})


def make_pipeline(entries, query=None, limit=None, include=None, exclude=None):
    """Build a Pipeline with a stub source and given config."""
    config = PipelineConfig(
        query=query,
        limit=limit,
        include_pattern=include,
        exclude_pattern=exclude,
    )
    pipeline = Pipeline(config)
    # Inject pre-built entries directly to bypass file I/O
    pipeline._entries = entries
    return pipeline


# ---------------------------------------------------------------------------
# PipelineConfig defaults
# ---------------------------------------------------------------------------

def test_pipeline_config_defaults():
    config = PipelineConfig()
    assert config.query is None
    assert config.limit is None
    assert config.include_pattern is None
    assert config.exclude_pattern is None


# ---------------------------------------------------------------------------
# process / process_to_list
# ---------------------------------------------------------------------------

def test_process_to_list_no_filter():
    entries = [make_entry(f"line {i}") for i in range(5)]
    pipeline = make_pipeline(entries)
    result = pipeline.process_to_list()
    assert len(result) == 5


def test_process_applies_limit():
    entries = [make_entry(f"line {i}") for i in range(10)]
    pipeline = make_pipeline(entries, limit=3)
    result = pipeline.process_to_list()
    assert len(result) == 3


def test_process_applies_include_pattern():
    entries = [
        make_entry("ERROR something went wrong"),
        make_entry("INFO all good"),
        make_entry("ERROR another failure"),
    ]
    pipeline = make_pipeline(entries, include="ERROR")
    result = pipeline.process_to_list()
    assert len(result) == 2
    assert all("ERROR" in e.raw for e in result)


def test_process_applies_exclude_pattern():
    entries = [
        make_entry("DEBUG verbose stuff"),
        make_entry("INFO useful info"),
        make_entry("DEBUG more noise"),
    ]
    pipeline = make_pipeline(entries, exclude="DEBUG")
    result = pipeline.process_to_list()
    assert len(result) == 1
    assert result[0].raw == "INFO useful info"


def test_process_include_and_exclude_combined():
    entries = [
        make_entry("ERROR from service-a"),
        make_entry("ERROR from service-b"),
        make_entry("INFO from service-a"),
    ]
    pipeline = make_pipeline(entries, include="ERROR", exclude="service-b")
    result = pipeline.process_to_list()
    assert len(result) == 1
    assert "service-a" in result[0].raw


def test_process_applies_query_filter():
    entries = [
        make_entry("200 OK", groups={"status": "200"}),
        make_entry("404 Not Found", groups={"status": "404"}),
        make_entry("200 OK again", groups={"status": "200"}),
    ]
    condition = QueryCondition(field="status", operator="eq", value="404")
    query = Query(conditions=[condition])
    pipeline = make_pipeline(entries, query=query)
    result = pipeline.process_to_list()
    assert len(result) == 1
    assert result[0].groups["status"] == "404"


def test_process_limit_applied_after_filters():
    """Limit should apply to the already-filtered result set."""
    entries = [
        make_entry(f"ERROR line {i}", groups={"level": "ERROR"})
        for i in range(8)
    ] + [
        make_entry(f"INFO line {i}", groups={"level": "INFO"})
        for i in range(4)
    ]
    pipeline = make_pipeline(entries, include="ERROR", limit=5)
    result = pipeline.process_to_list()
    assert len(result) == 5
    assert all("ERROR" in e.raw for e in result)


def test_process_returns_empty_on_no_match():
    entries = [make_entry("INFO nothing special") for _ in range(3)]
    pipeline = make_pipeline(entries, include="CRITICAL")
    result = pipeline.process_to_list()
    assert result == []


def test_process_generator_yields_same_as_list():
    entries = [make_entry(f"line {i}") for i in range(4)]
    pipeline = make_pipeline(entries)
    from_generator = list(pipeline.process())
    from_list = pipeline.process_to_list()
    assert [e.raw for e in from_generator] == [e.raw for e in from_list]
