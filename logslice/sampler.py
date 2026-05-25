"""Log entry sampling utilities for reducing high-volume log streams."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class SampleConfig:
    """Configuration for log sampling."""

    rate: float = 1.0  # fraction of entries to keep, 0.0–1.0
    max_entries: Optional[int] = None  # hard cap on total entries yielded
    seed: Optional[int] = None  # random seed for reproducibility

    def __post_init__(self) -> None:
        if not (0.0 < self.rate <= 1.0):
            raise ValueError(f"rate must be in (0.0, 1.0], got {self.rate}")
        if self.max_entries is not None and self.max_entries < 1:
            raise ValueError(
                f"max_entries must be a positive integer, got {self.max_entries}"
            )


class Sampler:
    """Samples a stream of LogEntry objects according to a SampleConfig."""

    def __init__(self, config: Optional[SampleConfig] = None) -> None:
        self._config = config or SampleConfig()
        self._rng = random.Random(self._config.seed)

    @property
    def config(self) -> SampleConfig:
        return self._config

    def sample(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield a sampled subset of *entries* according to the config."""
        count = 0
        max_entries = self._config.max_entries
        rate = self._config.rate

        for entry in entries:
            if max_entries is not None and count >= max_entries:
                break
            if rate >= 1.0 or self._rng.random() < rate:
                yield entry
                count += 1

    def sample_to_list(self, entries: Iterable[LogEntry]) -> List[LogEntry]:
        """Return sampled entries as a list."""
        return list(self.sample(entries))
