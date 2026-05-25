"""Tests for logslice.sampler."""

import pytest

from logslice.parser import LogEntry
from logslice.sampler import SampleConfig, Sampler


def make_entry(raw: str = "line") -> LogEntry:
    return LogEntry(raw=raw, groups={})


def make_entries(n: int) -> list:
    return [make_entry(f"line {i}") for i in range(n)]


# ---------------------------------------------------------------------------
# SampleConfig validation
# ---------------------------------------------------------------------------

def test_default_config_rate_is_one():
    cfg = SampleConfig()
    assert cfg.rate == 1.0


def test_invalid_rate_zero_raises():
    with pytest.raises(ValueError, match="rate"):
        SampleConfig(rate=0.0)


def test_invalid_rate_above_one_raises():
    with pytest.raises(ValueError, match="rate"):
        SampleConfig(rate=1.5)


def test_invalid_max_entries_raises():
    with pytest.raises(ValueError, match="max_entries"):
        SampleConfig(max_entries=0)


# ---------------------------------------------------------------------------
# Sampler behaviour
# ---------------------------------------------------------------------------

def test_full_rate_returns_all_entries():
    entries = make_entries(10)
    sampler = Sampler(SampleConfig(rate=1.0))
    result = sampler.sample_to_list(entries)
    assert result == entries


def test_max_entries_caps_output():
    entries = make_entries(50)
    sampler = Sampler(SampleConfig(rate=1.0, max_entries=10))
    result = sampler.sample_to_list(entries)
    assert len(result) == 10


def test_max_entries_larger_than_stream_returns_all():
    entries = make_entries(5)
    sampler = Sampler(SampleConfig(rate=1.0, max_entries=100))
    result = sampler.sample_to_list(entries)
    assert len(result) == 5


def test_sample_is_reproducible_with_seed():
    entries = make_entries(100)
    cfg = SampleConfig(rate=0.3, seed=42)
    result_a = Sampler(cfg).sample_to_list(entries)
    result_b = Sampler(cfg).sample_to_list(entries)
    assert result_a == result_b


def test_sample_rate_roughly_correct():
    entries = make_entries(1000)
    sampler = Sampler(SampleConfig(rate=0.5, seed=0))
    result = sampler.sample_to_list(entries)
    # Allow generous tolerance for randomness
    assert 350 <= len(result) <= 650


def test_sample_returns_iterator():
    entries = make_entries(5)
    sampler = Sampler()
    it = sampler.sample(entries)
    assert hasattr(it, "__iter__") and hasattr(it, "__next__")


def test_empty_input_returns_empty():
    sampler = Sampler(SampleConfig(rate=0.5, seed=1))
    result = sampler.sample_to_list([])
    assert result == []
