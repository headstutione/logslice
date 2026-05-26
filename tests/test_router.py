"""Tests for logslice.router."""

import pytest

from logslice.parser import LogEntry
from logslice.router import RouteRule, RouterConfig, Router


def make_entry(raw: str, **groups: str) -> LogEntry:
    return LogEntry(raw=raw, groups=dict(groups))


# ---------------------------------------------------------------------------
# RouteRule
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid pattern"):
        RouteRule(destination="x", pattern="[invalid")


def test_rule_matches_raw_line():
    rule = RouteRule(destination="errors", pattern=r"ERROR")
    assert rule.matches(make_entry("2024-01-01 ERROR something broke"))


def test_rule_no_match_raw_line():
    rule = RouteRule(destination="errors", pattern=r"ERROR")
    assert not rule.matches(make_entry("2024-01-01 INFO all good"))


def test_rule_matches_named_field():
    rule = RouteRule(destination="errors", pattern=r"ERROR", field="level")
    entry = make_entry("raw line", level="ERROR")
    assert rule.matches(entry)


def test_rule_field_missing_falls_back_to_raw():
    rule = RouteRule(destination="errors", pattern=r"ERROR", field="level")
    entry = make_entry("raw ERROR line")  # no 'level' group
    assert rule.matches(entry)


# ---------------------------------------------------------------------------
# Router — basic routing
# ---------------------------------------------------------------------------

def _make_router(*rules: RouteRule, default="default", stop=True) -> Router:
    cfg = RouterConfig(rules=list(rules), default_destination=default, stop_on_first_match=stop)
    return Router(cfg)


def test_route_returns_default_when_no_rules_match():
    router = _make_router(RouteRule("errors", r"ERROR"))
    dest = router.route(make_entry("INFO nothing here"))
    assert dest == "default"


def test_route_returns_matching_destination():
    router = _make_router(RouteRule("errors", r"ERROR"))
    dest = router.route(make_entry("ERROR boom"))
    assert dest == "errors"


def test_sink_is_called_on_match():
    collected = []
    router = _make_router(RouteRule("errors", r"ERROR"))
    router.register("errors", collected.append)

    entry = make_entry("ERROR boom")
    router.route(entry)
    assert collected == [entry]


def test_sink_not_called_for_wrong_destination():
    collected = []
    router = _make_router(RouteRule("errors", r"ERROR"))
    router.register("warnings", collected.append)

    router.route(make_entry("ERROR boom"))
    assert collected == []


def test_stop_on_first_match_prevents_second_rule():
    router = _make_router(
        RouteRule("first", r"MATCH"),
        RouteRule("second", r"MATCH"),
        stop=True,
    )
    dest = router.route(make_entry("MATCH"))
    assert dest == "first"


def test_no_stop_on_first_match_uses_last_rule():
    router = _make_router(
        RouteRule("first", r"MATCH"),
        RouteRule("second", r"MATCH"),
        stop=False,
    )
    dest = router.route(make_entry("MATCH"))
    assert dest == "second"


def test_route_many_groups_entries():
    router = _make_router(RouteRule("errors", r"ERROR"))
    entries = [
        make_entry("ERROR one"),
        make_entry("INFO two"),
        make_entry("ERROR three"),
    ]
    result = router.route_many(entries)
    assert len(result["errors"]) == 2
    assert len(result["default"]) == 1


def test_multiple_sinks_per_destination():
    a, b = [], []
    router = _make_router(RouteRule("x", r"X"))
    router.register("x", a.append)
    router.register("x", b.append)

    entry = make_entry("X marks the spot")
    router.route(entry)
    assert a == [entry] and b == [entry]
