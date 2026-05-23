"""Tests for the CLI export argument parsing and config building utilities."""

import argparse
import pytest
import os
import tempfile

from logslice.cli_export import add_export_args, build_export_config, write_export
from logslice.exporter import ExportConfig, ExportFormat
from logslice.parser import LogEntry


def _make_args(**kwargs):
    """Create a minimal argparse Namespace with export-related defaults."""
    defaults = {
        "export_format": None,
        "export_output": None,
        "export_pretty": False,
        "export_fields": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def make_entry(raw="ERROR something went wrong", groups=None):
    """Helper to create a LogEntry for testing."""
    return LogEntry(raw=raw, groups=groups or {"level": "ERROR", "msg": "something went wrong"})


# ---------------------------------------------------------------------------
# add_export_args
# ---------------------------------------------------------------------------

def test_add_export_args_adds_format_flag():
    parser = argparse.ArgumentParser()
    add_export_args(parser)
    args = parser.parse_args(["--export-format", "json"])
    assert args.export_format == "json"


def test_add_export_args_adds_output_flag():
    parser = argparse.ArgumentParser()
    add_export_args(parser)
    args = parser.parse_args(["--export-output", "/tmp/out.txt"])
    assert args.export_output == "/tmp/out.txt"


def test_add_export_args_adds_pretty_flag():
    parser = argparse.ArgumentParser()
    add_export_args(parser)
    args = parser.parse_args(["--export-pretty"])
    assert args.export_pretty is True


def test_add_export_args_pretty_defaults_false():
    parser = argparse.ArgumentParser()
    add_export_args(parser)
    args = parser.parse_args([])
    assert args.export_pretty is False


def test_add_export_args_adds_fields_flag():
    parser = argparse.ArgumentParser()
    add_export_args(parser)
    args = parser.parse_args(["--export-fields", "level", "msg"])
    assert args.export_fields == ["level", "msg"]


# ---------------------------------------------------------------------------
# build_export_config
# ---------------------------------------------------------------------------

def test_build_export_config_returns_none_when_no_format():
    args = _make_args(export_format=None)
    config = build_export_config(args)
    assert config is None


def test_build_export_config_text_format():
    args = _make_args(export_format="text")
    config = build_export_config(args)
    assert isinstance(config, ExportConfig)
    assert config.format == ExportFormat.TEXT


def test_build_export_config_json_format():
    args = _make_args(export_format="json")
    config = build_export_config(args)
    assert config.format == ExportFormat.JSON


def test_build_export_config_csv_format():
    args = _make_args(export_format="csv")
    config = build_export_config(args)
    assert config.format == ExportFormat.CSV


def test_build_export_config_sets_pretty():
    args = _make_args(export_format="json", export_pretty=True)
    config = build_export_config(args)
    assert config.pretty is True


def test_build_export_config_sets_fields():
    args = _make_args(export_format="csv", export_fields=["level", "msg"])
    config = build_export_config(args)
    assert config.fields == ["level", "msg"]


def test_build_export_config_invalid_format_raises():
    args = _make_args(export_format="xml")
    with pytest.raises((ValueError, KeyError)):
        build_export_config(args)


# ---------------------------------------------------------------------------
# write_export
# ---------------------------------------------------------------------------

def test_write_export_to_stdout(capsys):
    entries = [make_entry()]
    config = ExportConfig(format=ExportFormat.TEXT)
    write_export(entries, config, output_path=None)
    captured = capsys.readouterr()
    assert "ERROR something went wrong" in captured.out


def test_write_export_to_file():
    entries = [make_entry(raw="INFO all good", groups={"level": "INFO", "msg": "all good"})]
    config = ExportConfig(format=ExportFormat.TEXT)
    with tempfile.NamedTemporaryFile(mode="r", suffix=".txt", delete=False) as f:
        path = f.name
    try:
        write_export(entries, config, output_path=path)
        with open(path) as f:
            content = f.read()
        assert "INFO all good" in content
    finally:
        os.unlink(path)


def test_write_export_json_to_file():
    entries = [make_entry()]
    config = ExportConfig(format=ExportFormat.JSON, pretty=False)
    with tempfile.NamedTemporaryFile(mode="r", suffix=".json", delete=False) as f:
        path = f.name
    try:
        write_export(entries, config, output_path=path)
        with open(path) as f:
            content = f.read()
        assert "ERROR" in content
    finally:
        os.unlink(path)
