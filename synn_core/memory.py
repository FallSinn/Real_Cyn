"""Memory management subsystem using SQLite for persistence."""
from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .logging_util import emit_state, log_scope, setup_logging


MEMORY_DB_PATH = Path("synn_core_memory.sqlite3")


@dataclass
class MemoryRecord:
    """Generic memory record."""

    kind: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)


class MemoryStore:
    """Thread-safe SQLite-backed memory store."""

    def __init__(self, path: Path = MEMORY_DB_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._ensure_tables()
        self.logger = setup_logging()

    def _ensure_tables(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    importance REAL,
                    created_at REAL
                )
                """
            )

    def add(self, record: MemoryRecord) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT INTO memories (kind, content, metadata, importance, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    record.kind,
                    record.content,
                    str(record.metadata),
                    record.importance,
                    record.created_at,
                ),
            )
            memory_id = cursor.lastrowid
            self.logger.debug("Memory added", extra={"memory_id": memory_id})
            return memory_id

    def fetch(self, kind: Optional[str] = None, limit: int = 10) -> List[MemoryRecord]:
        query = "SELECT kind, content, metadata, importance, created_at FROM memories"
        params: Tuple[Any, ...] = ()
        if kind:
            query += " WHERE kind = ?"
            params = (kind,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params += (limit,)
        with self._lock:
            cursor = self._connection.execute(query, params)
            rows = cursor.fetchall()
        records = [
            MemoryRecord(
                kind=row["kind"],
                content=row["content"],
                metadata=eval(row["metadata"]) if row["metadata"] else {},
                importance=row["importance"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return records

    def search(self, keyword: str, limit: int = 5) -> List[MemoryRecord]:
        with self._lock:
            cursor = self._connection.execute(
                "SELECT kind, content, metadata, importance, created_at FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{keyword}%", limit),
            )
            rows = cursor.fetchall()
        return [
            MemoryRecord(
                kind=row["kind"],
                content=row["content"],
                metadata=eval(row["metadata"]) if row["metadata"] else {},
                importance=row["importance"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def wipe(self) -> None:
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM memories")


class MemorySubsystem:
    """High-level memory subsystem grouping different memory types."""

    def __init__(self, store: Optional[MemoryStore] = None) -> None:
        self.store = store or MemoryStore()
        self.working_memory: List[str] = []
        self.logger = setup_logging()

    def add_short_term(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        metadata = metadata or {}
        record = MemoryRecord(kind="short_term", content=content, metadata=metadata)
        self.store.add(record)
        self.logger.debug("Short term memory added", extra={"content": content})

    def add_working_memory(self, content: str) -> None:
        self.working_memory.append(content)
        if len(self.working_memory) > 10:
            self.working_memory.pop(0)
        self.logger.debug("Working memory updated", extra={"content": content})

    def add_episodic_memory(self, content: str, importance: float = 0.5) -> None:
        record = MemoryRecord(kind="episodic", content=content, importance=importance)
        self.store.add(record)

    def add_semantic_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        record = MemoryRecord(kind="semantic", content=content, metadata=metadata or {})
        self.store.add(record)

    def retrieve_context(self, keyword: str, limit: int = 5) -> List[MemoryRecord]:
        with log_scope(self.logger, "retrieve_context", keyword=keyword, limit=limit):
            results = self.store.search(keyword, limit=limit)
            emit_state(
                "memory",
                operation="retrieve_context",
                keyword=keyword,
                retrieved=[record.content for record in results],
            )
            return results

    def summarize_working_memory(self) -> str:
        if not self.working_memory:
            return ""
        return " | ".join(self.working_memory[-5:])

    def decay_working_memory(self) -> None:
        if self.working_memory:
            self.working_memory = self.working_memory[-5:]


__all__ = ["MemoryRecord", "MemoryStore", "MemorySubsystem", "MEMORY_DB_PATH"]
