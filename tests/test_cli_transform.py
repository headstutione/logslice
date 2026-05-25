"""Tests for logslice.cli_transform."""
import argparse

import pytest

from logslice.cli_transform import (
    _parse_single,
    add_transform_args,
    build_transformer,
)
from logslice.parser import LogEntry


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_transform_args(p)
    return p


def make_entry(**groups: str) -> LogEntry:
    return LogEntry(raw="raw", groups=groups if groups else None)


# ---------------------------------------------------------------------------
# add_transform_args
# ---------------------------------------------------------------------------

def test_add_transform_args_adds_transform_flag():
    p = _make_parser()
    args = p.parse_args([])
    assert hasattr(args, "transforms")


def test_add_transform_args_default_is_empty_list():
    p = _make_parser()
    args = p.parse_args([])
    assert args.transforms == []


def test_add_transform_args_adds_stop_on_error_flag():
    p = _make_parser()
    args = p.parse_args([])
    assert args.transform_stop_on_error is False


def test_stop_on_error_flag_can_be_set():
    p = _make_parser()
    args = p.parse_args(["--transform-stop-on-error"])
    assert args.transform_stop_on_error is True


def test_multiple_transforms_accumulated():
    p = _make_parser()
    args = p.parse_args(["--transform", "level:uppercase", "--transform", "msg:strip"])
    assert len(args.transforms) == 2


# ---------------------------------------------------------------------------
# _parse_single
# ---------------------------------------------------------------------------

def test_parse_single_uppercase():
    rule = _parse_single("level:uppercase")
    assert rule.field == "level"
    assert rule.transform("info") == "INFO"


def test_parse_single_lowercase():
    rule = _parse_single("level:lowercase")
    assert rule.transform("ERROR") == "error"


def test_parse_single_strip():
    rule = _parse_single("msg:strip")
    assert rule.transform("  hi  ") == "hi"


def test_parse_single_regex_replace():
    rule = _parse_single(r"msg:regex_replace=\d+:NUM")
    assert rule.transform("error 404") == "error NUM"


def test_parse_single_missing_colon_raises():
    with pytest.raises(argparse.ArgumentTypeError, match="expected FIELD:OP"):
        _parse_single("leveluppercase")


def test_parse_single_unknown_op_raises():
    with pytest.raises(argparse.ArgumentTypeError, match="Unknown transform"):
        _parse_single("level:explode")


def test_parse_single_regex_replace_missing_replacement_raises():
    with pytest.raises(argparse.ArgumentTypeError, match="PATTERN:REPLACEMENT"):
        _parse_single("msg:regex_replace=nocohere")


# ---------------------------------------------------------------------------
# build_transformer
# ---------------------------------------------------------------------------

def test_build_transformer_no_transforms_returns_identity():
    p = _make_parser()
    args = p.parse_args([])
    t = build_transformer(args)
    entry = make_entry(level="info")
    assert t.transform(entry).groups["level"] == "info"


def test_build_transformer_applies_rule():
    p = _make_parser()
    args = p.parse_args(["--transform", "level:uppercase"])
    t = build_transformer(args)
    entry = make_entry(level="debug")
    assert t.transform(entry).groups["level"] == "DEBUG"


def test_build_transformer_stop_on_error_propagated():
    p = _make_parser()
    args = p.parse_args(["--transform-stop-on-error"])
    t = build_transformer(args)
    assert t.config.stop_on_error is True
