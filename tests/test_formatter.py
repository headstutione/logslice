"""Tests for logslice.formatter module."""

import json
import pytest
from logslice.parser import LogEntry
from logslice.formatter import Formatter, JsonFormatter, DEFAULT_FORMAT


def make_entry(line_number=1, raw="2024-01-10 ERROR msg\n", groups=None):
    return LogEntry(line_number=line_number, raw=raw, groups=groups or {})


def test_default_format():
    fmt = Formatter()
    entry = make_entry(line_number=3, raw="hello\n")
    result = fmt.format_entry(entry)
    assert result == "3\thello"


def test_custom_template():
    fmt = Formatter(template="[{line_number}] {raw}")
    entry = make_entry(line_number=7, raw="world\n")
    assert fmt.format_entry(entry) == "[7] world"


def test_template_with_groups():
    fmt = Formatter(template="{level}: {msg}")
    entry = make_entry(groups={"level": "ERROR", "msg": "bad thing"})
    assert fmt.format_entry(entry) == "ERROR: bad thing"


def test_template_missing_key_raises():
    fmt = Formatter(template="{nonexistent}")
    entry = make_entry()
    with pytest.raises(ValueError, match="nonexistent"):
        fmt.format_entry(entry)


def test_render_multiple_entries():
    fmt = Formatter(template="{raw}")
    entries = [make_entry(raw="line1\n"), make_entry(raw="line2\n")]
    result = fmt.render(entries)
    assert result == "line1\nline2"


def test_json_formatter_basic():
    fmt = JsonFormatter()
    entry = make_entry(line_number=5, raw="test line\n")
    result = json.loads(fmt.format_entry(entry))
    assert result["line_number"] == 5
    assert result["raw"] == "test line"
    assert "groups" not in result


def test_json_formatter_with_groups():
    fmt = JsonFormatter()
    entry = make_entry(groups={"level": "INFO"})
    result = json.loads(fmt.format_entry(entry))
    assert result["groups"] == {"level": "INFO"}


def test_json_formatter_render():
    fmt = JsonFormatter()
    entries = [make_entry(line_number=i) for i in range(1, 4)]
    lines = fmt.render(entries).splitlines()
    assert len(lines) == 3
    assert all(json.loads(l)["line_number"] == i + 1 for i, l in enumerate(lines))
