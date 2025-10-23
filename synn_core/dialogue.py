"""Dialogue management for Synn Core."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .cognition import CognitionSubsystem, Plan, PlanStep
from .emotions import EmotionState, HormoneSubsystem
from .logging_util import emit_state
from .memory import MemorySubsystem
from .needs import NeedsSubsystem
from .persona import PersonaSubsystem
from .reflection import ReflectionLoop
from .scorecard import HumanityScorecard
from .safety import EthicsEngine


@dataclass
class DialogueTurn:
    user_message: str
    agent_response: str
    action: str


class DialogueManager:
    """Coordinates subsystems to process dialogue turns."""

    def __init__(
        self,
        memory: MemorySubsystem,
        hormones: HormoneSubsystem,
        needs: NeedsSubsystem,
        persona: PersonaSubsystem,
        cognition: CognitionSubsystem,
        reflection: ReflectionLoop,
        ethics: EthicsEngine,
        scorecard: HumanityScorecard | None = None,
    ) -> None:
        self.memory = memory
        self.hormones = hormones
        self.needs = needs
        self.persona = persona
        self.cognition = cognition
        self.reflection = reflection
        self.ethics = ethics
        self.last_plan: Optional[Plan] = None
        self.last_emotion: Optional[EmotionState] = None
        self.scorecard = scorecard

    def process(self, user_message: str) -> DialogueTurn:
        influences = self.hormones.apply_event(user_message)
        self.hormones.tick(influences)
        emotion_state = self.hormones.derive_emotion()
        emotion_dict = {
            "valence": emotion_state.valence,
            "arousal": emotion_state.arousal,
            "dominance": emotion_state.dominance,
        }
        if self.scorecard:
            self.scorecard.observe_affective(self.hormones.to_dict(), emotion_dict)
        self.needs.tick()
        persona_summary = self.persona.summary()
        plan = self.cognition.plan_response(user_message)
        chosen_step = self._select_plan_step(plan)
        bias = self.reflection.get_bias(chosen_step.action)
        chosen_step.confidence += bias
        ethics_decision = self.ethics.evaluate(chosen_step.action)
        if not ethics_decision.allowed:
            chosen_step = PlanStep(description="Seek safe alternative", action="ask_question", confidence=0.4)
        response = self.cognition.realize_response(chosen_step, emotion_dict, persona_summary)
        self.needs.apply_action(chosen_step.action)
        self.memory.add_short_term(user_message)
        self.memory.add_episodic_memory(f"User: {user_message} | Agent: {response}")
        self.memory.add_working_memory(f"Action taken: {chosen_step.action}")
        self.last_plan = plan
        self.last_emotion = emotion_state
        turn = DialogueTurn(user_message=user_message, agent_response=response, action=chosen_step.action)
        if self.scorecard:
            self.scorecard.observe_dialogue(chosen_step.action, persona_summary)
        emit_state("dialogue", user_message=user_message, response=response, action=chosen_step.action)
        return turn

    def _select_plan_step(self, plan: Plan) -> PlanStep:
        if not plan.steps:
            return PlanStep(description="Default", action="ask_question", confidence=0.5)
        scored_steps = []
        for step in plan.steps:
            bias = self.reflection.get_bias(step.action)
            scored_steps.append((step.confidence + bias, step))
        scored_steps.sort(key=lambda item: item[0], reverse=True)
        best = scored_steps[0][1]
        plan.steps.remove(best)
        return best

    def reflect(self, turn: DialogueTurn) -> None:
        result = self.reflection.review(turn.agent_response, turn.user_message, turn.action)
        self.memory.add_semantic_memory(f"Reflection: {result.feedback}")
        if self.scorecard:
            self.scorecard.observe_reflection(result.feedback, result.action_bias)


__all__ = ["DialogueManager", "DialogueTurn"]
