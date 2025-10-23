"""Persona and identity subsystem."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List

from .logging_util import emit_state


BIG_FIVE_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


@dataclass
class TraitState:
    name: str
    value: float
    drift_rate: float

    def drift(self) -> None:
        change = (random.random() - 0.5) * self.drift_rate
        self.value = max(0.0, min(1.0, self.value + change))


@dataclass
class Persona:
    """Persona representation using Big Five traits."""

    traits: Dict[str, TraitState]
    narrative: str
    roles: List[str] = field(default_factory=list)

    def drift(self) -> None:
        for trait in self.traits.values():
            trait.drift()
        emit_state("persona", traits={name: trait.value for name, trait in self.traits.items()})

    def describe(self) -> str:
        lines = [f"Trait {name}: {state.value:.2f}" for name, state in self.traits.items()]
        return "; ".join(lines)


class PersonaSubsystem:
    def __init__(self) -> None:
        traits = {
            name: TraitState(name=name, value=0.5 + (random.random() - 0.5) * 0.1, drift_rate=0.02)
            for name in BIG_FIVE_TRAITS
        }
        self.persona = Persona(traits=traits, narrative="Curious systems architect", roles=["guide", "analyst"])

    def tick(self) -> None:
        self.persona.drift()

    def summary(self) -> str:
        return self.persona.describe()


__all__ = ["Persona", "TraitState", "PersonaSubsystem", "BIG_FIVE_TRAITS"]
