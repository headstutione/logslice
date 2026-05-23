"""Tests for the FileWatcher module."""

import time
import threading
import tempfile
import os
from unittest.mock import MagicMock, patch

import pytest

from logslice.watcher import WatchConfig, WatchError, FileWatcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: str, text: str) -> None:
    """Append *text* to *path*, creating it if necessary."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# WatchConfig
# ---------------------------------------------------------------------------

class TestWatchConfig:
    def test_defaults(self):
        cfg = WatchConfig(path="app.log")
        assert cfg.path == "app.log"
        assert cfg.poll_interval > 0
        assert cfg.max_lines is None
        assert cfg.follow is True

    def test_custom_values(self):
        cfg = WatchConfig(path="x.log", poll_interval=0.5, max_lines=100, follow=False)
        assert cfg.poll_interval == 0.5
        assert cfg.max_lines == 100
        assert cfg.follow is False


# ---------------------------------------------------------------------------
# WatchError
# ---------------------------------------------------------------------------

class TestWatchError:
    def test_is_exception(self):
        err = WatchError("boom")
        assert isinstance(err, Exception)
        assert "boom" in str(err)


# ---------------------------------------------------------------------------
# FileWatcher — construction
# ---------------------------------------------------------------------------

class TestFileWatcherInit:
    def test_raises_on_missing_file(self):
        cfg = WatchConfig(path="/nonexistent/file.log")
        with pytest.raises(WatchError):
            FileWatcher(cfg)

    def test_accepts_existing_file(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("line1\n")
        cfg = WatchConfig(path=str(log))
        watcher = FileWatcher(cfg)
        assert watcher is not None


# ---------------------------------------------------------------------------
# FileWatcher — reading new lines
# ---------------------------------------------------------------------------

class TestFileWatcherLines:
    def test_yields_new_lines_written_after_open(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("existing\n")

        cfg = WatchConfig(path=str(log), poll_interval=0.05, follow=True)
        watcher = FileWatcher(cfg)

        collected = []
        stop_event = threading.Event()

        def _run():
            for line in watcher.watch(stop_event=stop_event):
                collected.append(line)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        time.sleep(0.1)
        _write(str(log), "hello\n")
        _write(str(log), "world\n")
        time.sleep(0.2)
        stop_event.set()
        t.join(timeout=2)

        assert "hello\n" in collected
        assert "world\n" in collected

    def test_max_lines_stops_iteration(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("")

        cfg = WatchConfig(path=str(log), poll_interval=0.02, max_lines=3, follow=True)
        watcher = FileWatcher(cfg)

        collected = []
        stop_event = threading.Event()

        def _run():
            for line in watcher.watch(stop_event=stop_event):
                collected.append(line)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        time.sleep(0.05)
        for i in range(5):
            _write(str(log), f"line{i}\n")
        t.join(timeout=3)

        # Should have stopped after exactly max_lines
        assert len(collected) == 3

    def test_no_follow_reads_existing_content(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("alpha\nbeta\ngamma\n")

        cfg = WatchConfig(path=str(log), follow=False)
        watcher = FileWatcher(cfg)

        lines = list(watcher.watch())
        assert lines == ["alpha\n", "beta\n", "gamma\n"]
