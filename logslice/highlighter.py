"""Terminal color highlighting for matched log output."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

ANSI_RESET = "\033[0m"

COLOR_MAP = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bold": "\033[1m",
}


@dataclass
class HighlightRule:
    """A single highlight rule: pattern + color."""

    pattern: str
    color: str = "yellow"
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.color not in COLOR_MAP:
            raise ValueError(
                f"Unknown color {self.color!r}. Choose from: {sorted(COLOR_MAP)}"
            )
        self._compiled = re.compile(self.pattern)

    def apply(self, text: str) -> str:
        """Return *text* with all matches wrapped in ANSI color codes."""
        color_code = COLOR_MAP[self.color]

        def _wrap(m: re.Match) -> str:  # type: ignore[type-arg]
            return f"{color_code}{m.group(0)}{ANSI_RESET}"

        return self._compiled.sub(_wrap, text)  # type: ignore[union-attr]


@dataclass
class HighlightConfig:
    """Collection of highlight rules applied in order."""

    rules: List[HighlightRule] = field(default_factory=list)
    enabled: bool = True


class Highlighter:
    """Apply a :class:`HighlightConfig` to strings."""

    def __init__(self, config: Optional[HighlightConfig] = None) -> None:
        self.config = config or HighlightConfig()

    def highlight(self, text: str) -> str:
        """Return *text* with all configured rules applied."""
        if not self.config.enabled or not self.config.rules:
            return text
        for rule in self.config.rules:
            text = rule.apply(text)
        return text

    def highlight_many(self, lines: List[str]) -> List[str]:
        """Highlight each line in *lines* and return a new list."""
        return [self.highlight(line) for line in lines]
