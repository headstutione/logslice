"""Tests for logslice.report module."""
import pytest
from logslice.aggregator import AggregationConfig, AggregationResult
from logslice.report import ReportRenderer


def make_result(total, groups, group_by="level", top_n=None):
    cfg = AggregationConfig(group_by=group_by, top_n=top_n)
    r = AggregationResult(total=total, groups=groups, config=cfg)
    return r


def test_render_text_total_line():
    result = make_result(5, {})
    renderer = ReportRenderer()
    text = renderer.render_text(result)
    assert "Total entries: 5" in text


def test_render_text_with_groups():
    result = make_result(3, {"ERROR": 2, "INFO": 1})
    renderer = ReportRenderer()
    text = renderer.render_text(result)
    assert "ERROR" in text
    assert "INFO" in text
    assert "2" in text


def test_render_text_no_groups_no_breakdown():
    result = make_result(10, {}, group_by=None)
    renderer = ReportRenderer()
    text = renderer.render_text(result)
    assert "Breakdown" not in text


def test_render_csv_header():
    result = make_result(2, {"ERROR": 2}, group_by="level")
    renderer = ReportRenderer()
    csv = renderer.render_csv(result)
    lines = csv.splitlines()
    assert lines[0] == "level,count"


def test_render_csv_rows():
    result = make_result(3, {"ERROR": 2, "INFO": 1}, group_by="level")
    renderer = ReportRenderer()
    csv = renderer.render_csv(result)
    assert '"ERROR",2' in csv
    assert '"INFO",1' in csv


def test_render_csv_no_groups_shows_all():
    result = make_result(7, {}, group_by=None)
    renderer = ReportRenderer()
    csv = renderer.render_csv(result)
    assert '"(all)",7' in csv
