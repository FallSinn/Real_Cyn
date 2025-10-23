"""Emotion and hormone subsystem with slow dynamics."""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from .logging_util import DIAGNOSTICS, emit_state


HORMONE_NAMES = ["dopamine", "serotonin", "cortisol", "adrenaline", "endorphins"]


@dataclass
class HormoneState:
    """State for a single hormone."""

    level: float = 0.5
    baseline: float = 0.5
    decay: float = 0.01
    influence: Dict[str, float] = field(default_factory=dict)

    def update(self, delta: float) -> None:
        self.level = max(0.0, min(1.0, self.level + delta))

    def relax(self) -> None:
        self.level += (self.baseline - self.level) * self.decay
        self.level = max(0.0, min(1.0, self.level))


@dataclass
class EmotionState:
    """Aggregated emotional state derived from hormones."""

    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0


class HormoneSubsystem:
    """Model of hormones with slow dynamics and cross-influences."""

    def __init__(self) -> None:
        self.hormones: Dict[str, HormoneState] = {
            name: HormoneState()
            for name in HORMONE_NAMES
        }
        self.last_update = time.time()

    def tick(self, influences: Dict[str, float]) -> None:
        current = time.time()
        elapsed = current - self.last_update
        self.last_update = current
        for name, state in self.hormones.items():
            delta = influences.get(name, 0.0) * elapsed
            state.update(delta)
            state.relax()
        self._apply_cross_influences()
        emit_state("affective", hormones=self.to_dict())

    def _apply_cross_influences(self) -> None:
        for name, state in self.hormones.items():
            for other_name, weight in state.influence.items():
                other = self.hormones[other_name]
                other.update(weight * (state.level - other.level) * 0.1)

    def to_dict(self) -> Dict[str, float]:
        return {name: state.level for name, state in self.hormones.items()}

    def derive_emotion(self) -> EmotionState:
        dopamine = self.hormones["dopamine"].level
        serotonin = self.hormones["serotonin"].level
        cortisol = self.hormones["cortisol"].level
        adrenaline = self.hormones["adrenaline"].level
        endorphins = self.hormones["endorphins"].level
        valence = dopamine * 0.4 + serotonin * 0.4 - cortisol * 0.3
        arousal = adrenaline * 0.5 + cortisol * 0.2
        dominance = endorphins * 0.3 + dopamine * 0.2 - cortisol * 0.1
        DIAGNOSTICS.get("emotion_valence").add(valence)
        DIAGNOSTICS.get("emotion_arousal").add(arousal)
        DIAGNOSTICS.get("emotion_dominance").add(dominance)
        return EmotionState(valence=valence, arousal=arousal, dominance=dominance)

    def apply_event(self, event: str) -> Dict[str, float]:
        influences: Dict[str, float] = {name: 0.0 for name in HORMONE_NAMES}
        if "praise" in event:
            influences["dopamine"] += 0.05
            influences["endorphins"] += 0.03
        if "challenge" in event:
            influences["adrenaline"] += 0.04
            influences["cortisol"] += 0.02
        if "calm" in event:
            influences["serotonin"] += 0.05
            influences["cortisol"] -= 0.03
        if "stress" in event:
            influences["cortisol"] += 0.06
            influences["adrenaline"] += 0.04
        return influences


__all__ = ["HormoneSubsystem", "HormoneState", "EmotionState", "HORMONE_NAMES"]
