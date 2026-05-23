"""Tests for logslice.exporter."""

import json
import pytest

from logslice.exporter import Exporter, ExportConfig, ExportError
from logslice.parser import LogEntry


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_entry(raw: str, **groups) -> LogEntry:
    return LogEntry(raw=raw, groups=groups)


# ---------------------------------------------------------------------------
# text format
# ---------------------------------------------------------------------------

def test_text_format_returns_raw_lines():
    entries = [make_entry("line one"), make_entry("line two")]
    result = Exporter().export(entries)
    assert result == "line one\nline two"


def test_text_format_empty_list():
    assert Exporter().export([]) == ""


# ---------------------------------------------------------------------------
# json format
# ---------------------------------------------------------------------------

def test_json_format_includes_raw_and_groups():
    entries = [make_entry("2024-01-01 ERROR msg", level="ERROR", message="msg")]
    cfg = ExportConfig(format="json")
    result = json.loads(Exporter(cfg).export(entries))
    assert result[0]["raw"] == "2024-01-01 ERROR msg"
    assert result[0]["level"] == "ERROR"


def test_json_format_pretty():
    entries = [make_entry("hello")]
    cfg = ExportConfig(format="json", pretty_json=True)
    result = Exporter(cfg).export(entries)
    assert "\n" in result  # pretty-printed contains newlines


def test_json_format_field_filtering():
    entries = [make_entry("raw", level="INFO", message="ok")]
    cfg = ExportConfig(format="json", fields=["level"])
    result = json.loads(Exporter(cfg).export(entries))
    assert "level" in result[0]
    assert "message" not in result[0]
    assert "raw" not in result[0]


# ---------------------------------------------------------------------------
# csv format
# ---------------------------------------------------------------------------

def test_csv_format_has_header():
    entries = [make_entry("row", level="WARN")]
    cfg = ExportConfig(format="csv")
    result = Exporter(cfg).export(entries)
    lines = result.strip().splitlines()
    assert lines[0].startswith("raw")


def test_csv_format_empty_returns_empty_string():
    cfg = ExportConfig(format="csv")
    assert Exporter(cfg).export([]) == ""


def test_csv_custom_delimiter():
    entries = [make_entry("r", level="DEBUG")]
    cfg = ExportConfig(format="csv", delimiter="|")
    result = Exporter(cfg).export(entries)
    assert "|" in result


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------

def test_unknown_format_raises_export_error():
    cfg = ExportConfig(format="xml")
    with pytest.raises(ExportError, match="Unknown export format"):
        Exporter(cfg).export([])
