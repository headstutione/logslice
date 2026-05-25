"""Tests for logslice.highlighter."""
import pytest

from logslice.highlighter import (
    ANSI_RESET,
    COLOR_MAP,
    HighlightConfig,
    HighlightRule,
    Highlighter,
)


# ---------------------------------------------------------------------------
# HighlightRule
# ---------------------------------------------------------------------------

class TestHighlightRule:
    def test_invalid_color_raises(self):
        with pytest.raises(ValueError, match="Unknown color"):
            HighlightRule(pattern="error", color="purple")

    def test_apply_wraps_match(self):
        rule = HighlightRule(pattern="ERROR", color="red")
        result = rule.apply("[ERROR] something broke")
        assert COLOR_MAP["red"] in result
        assert ANSI_RESET in result
        assert "ERROR" in result

    def test_apply_no_match_returns_original(self):
        rule = HighlightRule(pattern="CRITICAL", color="red")
        text = "[INFO] all good"
        assert rule.apply(text) == text

    def test_apply_multiple_matches(self):
        rule = HighlightRule(pattern=r"\d+", color="cyan")
        result = rule.apply("line 42 col 7")
        assert result.count(COLOR_MAP["cyan"]) == 2
        assert result.count(ANSI_RESET) == 2


# ---------------------------------------------------------------------------
# HighlightConfig
# ---------------------------------------------------------------------------

class TestHighlightConfig:
    def test_defaults(self):
        cfg = HighlightConfig()
        assert cfg.rules == []
        assert cfg.enabled is True

    def test_disabled_flag(self):
        cfg = HighlightConfig(enabled=False)
        assert not cfg.enabled


# ---------------------------------------------------------------------------
# Highlighter
# ---------------------------------------------------------------------------

class TestHighlighter:
    def test_no_rules_returns_original(self):
        h = Highlighter(HighlightConfig(rules=[]))
        text = "[WARN] watch out"
        assert h.highlight(text) == text

    def test_disabled_config_returns_original(self):
        rule = HighlightRule(pattern="WARN", color="yellow")
        h = Highlighter(HighlightConfig(rules=[rule], enabled=False))
        text = "[WARN] watch out"
        assert h.highlight(text) == text

    def test_single_rule_applied(self):
        rule = HighlightRule(pattern="WARN", color="yellow")
        h = Highlighter(HighlightConfig(rules=[rule]))
        result = h.highlight("[WARN] watch out")
        assert COLOR_MAP["yellow"] in result

    def test_multiple_rules_applied_in_order(self):
        rules = [
            HighlightRule(pattern="ERROR", color="red"),
            HighlightRule(pattern=r"\d{3}", color="cyan"),
        ]
        h = Highlighter(HighlightConfig(rules=rules))
        result = h.highlight("ERROR code 500")
        assert COLOR_MAP["red"] in result
        assert COLOR_MAP["cyan"] in result

    def test_highlight_many(self):
        rule = HighlightRule(pattern="ok", color="green")
        h = Highlighter(HighlightConfig(rules=[rule]))
        lines = ["all ok here", "nothing here", "ok again"]
        results = h.highlight_many(lines)
        assert len(results) == 3
        assert COLOR_MAP["green"] in results[0]
        assert COLOR_MAP["green"] not in results[1]
        assert COLOR_MAP["green"] in results[2]

    def test_default_config_used_when_none_provided(self):
        h = Highlighter()
        assert h.highlight("test") == "test"
