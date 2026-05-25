"""Tests for logslice.transformer."""
import pytest

from logslice.parser import LogEntry
from logslice.transformer import (
    TransformError,
    TransformRule,
    Transformer,
    TransformerConfig,
    lowercase,
    regex_replace,
    strip_whitespace,
    uppercase,
)


def make_entry(raw: str = "raw line", **groups: str) -> LogEntry:
    return LogEntry(raw=raw, groups=groups if groups else None)


# ---------------------------------------------------------------------------
# TransformRule
# ---------------------------------------------------------------------------

class TestTransformRule:
    def test_apply_transforms_field(self):
        rule = TransformRule(field="level", transform=uppercase)
        entry = make_entry(level="info")
        result = rule.apply(entry)
        assert result.groups["level"] == "INFO"

    def test_apply_leaves_other_fields_unchanged(self):
        rule = TransformRule(field="level", transform=uppercase)
        entry = make_entry(level="info", msg="hello")
        result = rule.apply(entry)
        assert result.groups["msg"] == "hello"

    def test_apply_no_groups_returns_original(self):
        rule = TransformRule(field="level", transform=uppercase)
        entry = make_entry()
        result = rule.apply(entry)
        assert result is entry

    def test_apply_missing_field_returns_original(self):
        rule = TransformRule(field="missing", transform=uppercase)
        entry = make_entry(level="info")
        result = rule.apply(entry)
        assert result.groups == {"level": "info"}

    def test_raw_preserved(self):
        rule = TransformRule(field="level", transform=uppercase)
        entry = make_entry(raw="original raw", level="info")
        result = rule.apply(entry)
        assert result.raw == "original raw"


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------

class TestTransformer:
    def test_single_rule_applied(self):
        cfg = TransformerConfig(rules=[TransformRule("level", uppercase)])
        t = Transformer(cfg)
        result = t.transform(make_entry(level="debug"))
        assert result.groups["level"] == "DEBUG"

    def test_multiple_rules_applied_in_order(self):
        cfg = TransformerConfig(rules=[
            TransformRule("msg", strip_whitespace),
            TransformRule("msg", uppercase),
        ])
        t = Transformer(cfg)
        result = t.transform(make_entry(msg="  hello  "))
        assert result.groups["msg"] == "HELLO"

    def test_transform_all_returns_list(self):
        cfg = TransformerConfig(rules=[TransformRule("level", lowercase)])
        t = Transformer(cfg)
        entries = [make_entry(level="INFO"), make_entry(level="WARN")]
        results = t.transform_all(entries)
        assert [r.groups["level"] for r in results] == ["info", "warn"]

    def test_stop_on_error_raises_transform_error(self):
        def boom(v: str) -> str:
            raise ValueError("oops")

        cfg = TransformerConfig(
            rules=[TransformRule("level", boom, label="exploder")],
            stop_on_error=True,
        )
        t = Transformer(cfg)
        with pytest.raises(TransformError, match="exploder"):
            t.transform(make_entry(level="info"))

    def test_no_stop_on_error_ignores_failure(self):
        def boom(v: str) -> str:
            raise ValueError("oops")

        cfg = TransformerConfig(
            rules=[TransformRule("level", boom)],
            stop_on_error=False,
        )
        t = Transformer(cfg)
        entry = make_entry(level="info")
        result = t.transform(entry)
        # field unchanged because transform raised
        assert result.groups["level"] == "info"

    def test_config_property(self):
        cfg = TransformerConfig()
        t = Transformer(cfg)
        assert t.config is cfg


# ---------------------------------------------------------------------------
# Built-in helpers
# ---------------------------------------------------------------------------

def test_uppercase():
    assert uppercase("hello") == "HELLO"


def test_lowercase():
    assert lowercase("HELLO") == "hello"


def test_strip_whitespace():
    assert strip_whitespace("  hi  ") == "hi"


def test_regex_replace():
    fn = regex_replace(r"\d+", "NUM")
    assert fn("error 404 on line 12") == "error NUM on line NUM"
