"""Offline reconsolidation cycle."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List

from .logging_util import emit_state
from .memory import MemoryRecord, MemorySubsystem


@dataclass
class Dream:
    """Representation of an offline imaginative reconstruction."""

    narrative: str
    insights: List[str]


class Dreamer:
    def __init__(self, memory: MemorySubsystem) -> None:
        self.memory = memory

    def run(self) -> Dream:
        episodic = self.memory.store.fetch(kind="episodic", limit=5)
        semantic = self.memory.store.fetch(kind="semantic", limit=5)
        narrative_parts = [record.content for record in episodic + semantic]
        random.shuffle(narrative_parts)
        narrative = " -> ".join(narrative_parts) if narrative_parts else "Quiet reflection"
        insights = [f"Insight about {record.kind}: importance {record.importance}" for record in episodic]
        dream = Dream(narrative=narrative, insights=insights)
        emit_state("dreamer", narrative=narrative, insights=insights)
        return dream


__all__ = ["Dreamer", "Dream"]
