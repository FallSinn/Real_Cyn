"""Needs and drives subsystem."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .logging_util import emit_state


@dataclass
class Need:
    """Represents a single drive or need."""

    name: str
    level: float = 0.5
    target: float = 0.5
    priority: float = 0.5
    growth_rate: float = 0.01

    def tick(self) -> None:
        self.level += (self.target - self.level) * self.growth_rate
        self.level = max(0.0, min(1.0, self.level))

    def satisfy(self, amount: float) -> None:
        self.level = max(0.0, self.level - amount)


class NeedsSubsystem:
    """Manages drives and computes motivational weights."""

    def __init__(self) -> None:
        self.needs: Dict[str, Need] = {
            "curiosity": Need(name="curiosity", target=0.3, priority=0.6),
            "social_connection": Need(name="social_connection", target=0.4, priority=0.8),
            "competence": Need(name="competence", target=0.4, priority=0.7),
            "safety": Need(name="safety", target=0.2, priority=0.9),
        }

    def tick(self) -> None:
        for need in self.needs.values():
            need.tick()
        emit_state("needs", needs={name: need.level for name, need in self.needs.items()})

    def motivational_weights(self) -> Dict[str, float]:
        weights: Dict[str, float] = {}
        for name, need in self.needs.items():
            weights[name] = need.level * need.priority
        return weights

    def apply_action(self, action: str) -> None:
        if action == "offer_support":
            self.needs["social_connection"].satisfy(0.1)
        if action == "share_learning":
            self.needs["competence"].satisfy(0.1)
        if action == "ask_question":
            self.needs["curiosity"].satisfy(0.1)


__all__ = ["Need", "NeedsSubsystem"]
