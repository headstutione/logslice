"""File watcher module for logslice.

Provides tail-like functionality to monitor log files in real-time,
yielding new lines as they are appended.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, Optional

from logslice.parser import LogParser, ParseConfig
from logslice.pipeline import Pipeline, PipelineConfig


@dataclass
class WatchConfig:
    """Configuration for the file watcher."""

    # How often (in seconds) to poll the file for new content
    poll_interval: float = 0.25

    # Maximum number of lines to read from the end of the file on startup.
    # 0 means start from the current end (skip existing content).
    tail_lines: int = 0

    # If True, re-open the file when it appears to have been rotated
    # (i.e. its inode or size has decreased).
    follow_rotations: bool = True

    # Optional callback invoked with each new raw line string before parsing.
    on_raw_line: Optional[Callable[[str], None]] = field(default=None, repr=False)


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


class FileWatcher:
    """Watches a log file and yields parsed entries as new lines arrive.

    Example usage::

        watcher = FileWatcher("app.log", WatchConfig(tail_lines=10))
        for entry in watcher.watch():
            print(entry)
    """

    def __init__(
        self,
        filepath: str,
        watch_config: Optional[WatchConfig] = None,
        parse_config: Optional[ParseConfig] = None,
        pipeline_config: Optional[PipelineConfig] = None,
    ) -> None:
        self.filepath = filepath
        self.watch_config = watch_config or WatchConfig()
        self._parser = LogParser(parse_config or ParseConfig())
        self._pipeline_config = pipeline_config or PipelineConfig()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def watch(self) -> Generator:
        """Yield LogEntry objects for each new line appended to the file.

        This is a blocking generator; call it inside a thread or async task
        if you need non-blocking behaviour.

        Raises:
            WatchError: if the file cannot be opened or disappears.
        """
        if not os.path.exists(self.filepath):
            raise WatchError(f"File not found: {self.filepath}")

        pipeline = Pipeline(self._pipeline_config)

        with open(self.filepath, "r", encoding="utf-8", errors="replace") as fh:
            # Seek to the appropriate starting position.
            self._seek_start(fh)
            inode = self._get_inode()

            while True:
                line = fh.readline()

                if line:
                    if self.watch_config.on_raw_line:
                        self.watch_config.on_raw_line(line.rstrip("\n"))

                    entry = self._parser.parse_line(line.rstrip("\n"))
                    # Run the single entry through the pipeline filter.
                    results = list(pipeline.process(iter([entry])))
                    if results:
                        yield results[0]
                else:
                    # No new data — check for rotation then sleep.
                    if self.watch_config.follow_rotations:
                        new_inode = self._get_inode()
                        if new_inode != inode:
                            # File was rotated; re-open from the beginning.
                            fh.close()
                            fh = open(  # noqa: WPS515
                                self.filepath,
                                "r",
                                encoding="utf-8",
                                errors="replace",
                            )
                            inode = new_inode
                            continue

                    time.sleep(self.watch_config.poll_interval)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _seek_start(self, fh) -> None:
        """Position the file handle based on *tail_lines* setting."""
        if self.watch_config.tail_lines == 0:
            # Start from the current end of the file.
            fh.seek(0, os.SEEK_END)
            return

        # Read all lines and rewind to the nth-from-last.
        fh.seek(0)
        lines = fh.readlines()
        start_index = max(0, len(lines) - self.watch_config.tail_lines)
        if start_index == 0:
            fh.seek(0)
        else:
            # Seek to the byte offset of the desired line.
            offset = sum(len(l) for l in lines[:start_index])
            fh.seek(offset)

    def _get_inode(self) -> Optional[int]:
        """Return the inode of the watched file, or None on error."""
        try:
            return os.stat(self.filepath).st_ino
        except OSError:
            return None
