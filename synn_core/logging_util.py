"""Utilities for logging and tracing the Synn Core agent."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Deque, Dict, Generator, Iterable, List, Optional


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

TRACE_FILE = LOG_DIR / "trace.jsonl"


@dataclass
class TraceEvent:
    """Representation of an internal trace event."""

    timestamp: float
    layer: str
    state: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp,
            "layer": self.layer,
            "state": self.state,
        })


class TraceBuffer:
    """Thread-safe buffer that periodically writes trace events to disk."""

    def __init__(self, flush_interval: float = 5.0, maxlen: int = 256) -> None:
        self.flush_interval = flush_interval
        self.buffer: Deque[TraceEvent] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def add_event(self, event: TraceEvent) -> None:
        with self._lock:
            self.buffer.append(event)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.flush_interval)
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self.buffer:
                return
            TRACE_FILE.parent.mkdir(exist_ok=True)
            with TRACE_FILE.open("a", encoding="utf-8") as fh:
                while self.buffer:
                    fh.write(self.buffer.popleft().to_json() + "\n")

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=self.flush_interval * 2)
        self.flush()


TRACE_BUFFER = TraceBuffer()


def setup_logging() -> logging.Logger:
    """Configure the main logger for the Synn Core agent."""

    logger = logging.getLogger("synn_core")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        log_path = LOG_DIR / "synn_core.log"
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger


@contextmanager
def log_scope(logger: logging.Logger, message: str, **fields: Any) -> Generator[None, None, None]:
    """Context manager to log entering and exiting a scope."""

    logger.debug("ENTER %s %s", message, fields)
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.debug("EXIT %s elapsed=%.3f %s", message, elapsed, fields)


def log_trace(layer: str, state: Dict[str, Any]) -> None:
    """Record a trace event for internal state serialization."""

    event = TraceEvent(timestamp=time.time(), layer=layer, state=state)
    TRACE_BUFFER.add_event(event)


class RollingLog:
    """Small rolling log of recent agent messages."""

    def __init__(self, capacity: int = 64) -> None:
        self.capacity = capacity
        self.entries: Deque[Dict[str, Any]] = deque(maxlen=capacity)

    def add(self, **fields: Any) -> None:
        record = {"timestamp": time.time(), **fields}
        self.entries.append(record)

    def tail(self) -> List[Dict[str, Any]]:
        return list(self.entries)


@dataclass
class DiagnosticProbe:
    """Probe for collecting metrics across the pipeline."""

    name: str
    values: List[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.values.append(value)

    def mean(self) -> float:
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "mean": self.mean(), "values": list(self.values)}


class DiagnosticsRegistry:
    """Registry for diagnostic probes."""

    def __init__(self) -> None:
        self._probes: Dict[str, DiagnosticProbe] = {}

    def get(self, name: str) -> DiagnosticProbe:
        if name not in self._probes:
            self._probes[name] = DiagnosticProbe(name)
        return self._probes[name]

    def summary(self) -> Dict[str, Any]:
        return {name: probe.to_dict() for name, probe in self._probes.items()}


DIAGNOSTICS = DiagnosticsRegistry()


def emit_state(layer: str, **state: Any) -> None:
    """Emit state to the trace buffer and logs."""

    log_trace(layer, state)


def ensure_log_directory(path: Path) -> None:
    """Ensure the log directory exists."""

    path.mkdir(parents=True, exist_ok=True)


def cleanup_traces() -> None:
    """Remove existing trace files (useful for tests)."""

    if TRACE_FILE.exists():
        TRACE_FILE.unlink()


__all__ = [
    "TraceEvent",
    "TraceBuffer",
    "TRACE_BUFFER",
    "setup_logging",
    "log_scope",
    "log_trace",
    "RollingLog",
    "DiagnosticProbe",
    "DiagnosticsRegistry",
    "DIAGNOSTICS",
    "emit_state",
    "ensure_log_directory",
    "cleanup_traces",
]
