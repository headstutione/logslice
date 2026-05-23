"""Tests for the CLI entry point and argument parsing."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from logslice.cli import build_arg_parser, run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    """Return a namespace-like object with CLI defaults overridden by kwargs."""
    defaults = {
        "file": None,
        "include": [],
        "exclude": [],
        "query": None,
        "limit": None,
        "format": "text",
        "template": None,
        "group_by": None,
        "top": None,
        "output": None,
        "export_format": None,
        "pretty": False,
    }
    defaults.update(kwargs)
    ns = MagicMock()
    for k, v in defaults.items():
        setattr(ns, k, v)
    return ns


# ---------------------------------------------------------------------------
# Argument parser structure
# ---------------------------------------------------------------------------

def test_build_arg_parser_returns_parser():
    parser = build_arg_parser()
    assert parser is not None


def test_parser_accepts_file_argument():
    parser = build_arg_parser()
    args = parser.parse_args(["somefile.log"])
    assert args.file == "somefile.log"


def test_parser_accepts_include_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["f.log", "--include", "ERROR", "WARN"])
    assert "ERROR" in args.include
    assert "WARN" in args.include


def test_parser_accepts_exclude_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["f.log", "--exclude", "DEBUG"])
    assert "DEBUG" in args.exclude


def test_parser_accepts_limit_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["f.log", "--limit", "50"])
    assert args.limit == 50


def test_parser_accepts_query_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["f.log", "--query", "level=ERROR"])
    assert args.query == "level=ERROR"


def test_parser_accepts_format_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["f.log", "--format", "json"])
    assert args.format == "json"


# ---------------------------------------------------------------------------
# run() integration (mocked pipeline)
# ---------------------------------------------------------------------------

@patch("logslice.cli.Pipeline")
@patch("logslice.cli.LogParser")
def test_run_opens_file_and_processes(mock_parser_cls, mock_pipeline_cls, tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text("2024-01-01 ERROR something went wrong\n")

    mock_parser = MagicMock()
    mock_parser_cls.return_value = mock_parser

    mock_pipeline = MagicMock()
    mock_pipeline.process_to_list.return_value = []
    mock_pipeline_cls.return_value = mock_pipeline

    args = _make_args(file=str(log_file))

    # Should not raise
    run(args)

    mock_pipeline.process_to_list.assert_called_once()


@patch("logslice.cli.Pipeline")
@patch("logslice.cli.LogParser")
def test_run_prints_entries_to_stdout(mock_parser_cls, mock_pipeline_cls, tmp_path, capsys):
    log_file = tmp_path / "app.log"
    log_file.write_text("line one\nline two\n")

    mock_entry = MagicMock()
    mock_entry.raw = "line one"
    mock_entry.__str__ = lambda self: self.raw

    mock_parser = MagicMock()
    mock_parser_cls.return_value = mock_parser

    mock_pipeline = MagicMock()
    mock_pipeline.process_to_list.return_value = [mock_entry]
    mock_pipeline_cls.return_value = mock_pipeline

    args = _make_args(file=str(log_file))
    run(args)

    captured = capsys.readouterr()
    assert "line one" in captured.out


@patch("logslice.cli.Pipeline")
@patch("logslice.cli.LogParser")
def test_run_with_missing_file_raises(mock_parser_cls, mock_pipeline_cls):
    args = _make_args(file="/nonexistent/path/file.log")
    with pytest.raises((FileNotFoundError, OSError, SystemExit)):
        run(args)
