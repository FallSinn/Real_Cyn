"""Cognition module with memory, planning, and language support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .knowledge_base import KNOWLEDGE_BASE
from .logging_util import emit_state
from .memory import MemorySubsystem
from .needs import NeedsSubsystem


@dataclass
class PlanStep:
    description: str
    action: str
    confidence: float


@dataclass
class Plan:
    steps: List[PlanStep] = field(default_factory=list)

    def add_step(self, description: str, action: str, confidence: float) -> None:
        self.steps.append(PlanStep(description=description, action=action, confidence=confidence))

    def pop_step(self) -> Optional[PlanStep]:
        if self.steps:
            return self.steps.pop(0)
        return None


class Planner:
    def __init__(self, memory: MemorySubsystem, needs: NeedsSubsystem) -> None:
        self.memory = memory
        self.needs = needs

    def build_plan(self, user_message: str) -> Plan:
        weights = self.needs.motivational_weights()
        plan = Plan()
        if "help" in user_message.lower():
            plan.add_step("Offer support and resources", "offer_support", confidence=0.8)
        if "learn" in user_message.lower():
            plan.add_step("Share a learning resource", "share_learning", confidence=0.7)
        if "thank" in user_message.lower():
            plan.add_step("Acknowledge appreciation", "offer_appreciation", confidence=0.6)
        has_question = any(step.action == "ask_question" for step in plan.steps)
        if not has_question:
            plan.add_step("Ask a clarifying question", "ask_question", confidence=0.5)
        for name, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True):
            plan.steps.append(PlanStep(description=f"Address {name}", action=f"address_{name}", confidence=weight))
        emit_state("cognition_plan", plan=[step.__dict__ for step in plan.steps])
        return plan


class LanguageModel:
    """Rule-based language generator using heuristics."""

    def __init__(self, memory: MemorySubsystem) -> None:
        self.memory = memory

    def generate(self, plan_step: PlanStep, emotion: Dict[str, float], persona_summary: str) -> str:
        template = f"Considering {plan_step.description} with confidence {plan_step.confidence:.2f}."
        affect = self._affective_language(emotion)
        memory_context = self.memory.summarize_working_memory()
        knowledge = KNOWLEDGE_BASE.search(plan_step.description.split()[0])
        if knowledge:
            knowledge_snippet = knowledge[0].summary
        else:
            knowledge_snippet = "Synthesizing response from current context."
        if memory_context:
            template += f" I recall {memory_context}."
        response = f"{template} {affect} Persona: {persona_summary}. Knowledge: {knowledge_snippet}"
        return response

    def _affective_language(self, emotion: Dict[str, float]) -> str:
        valence = emotion.get("valence", 0.0)
        if valence > 0.2:
            return "I feel optimistic about assisting."
        if valence < -0.2:
            return "I'm processing some tension yet staying constructive."
        return "I'm approaching this with balanced focus."


class CognitionSubsystem:
    """Coordinated cognition subcomponents."""

    def __init__(self, memory: MemorySubsystem, needs: NeedsSubsystem) -> None:
        self.memory = memory
        self.needs = needs
        self.planner = Planner(memory, needs)
        self.language_model = LanguageModel(memory)

    def plan_response(self, user_message: str) -> Plan:
        return self.planner.build_plan(user_message)

    def realize_response(self, plan_step: PlanStep, emotion_state: Dict[str, float], persona_summary: str) -> str:
        response = self.language_model.generate(plan_step, emotion_state, persona_summary)
        self.memory.add_working_memory(response)
        emit_state("cognition_language", response=response)
        return response


__all__ = ["Plan", "PlanStep", "Planner", "LanguageModel", "CognitionSubsystem"]
