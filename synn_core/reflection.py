"""Reflection loops for self-assessment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .logging_util import emit_state


@dataclass
class ReflectionResult:
    feedback: str
    adjustments: Dict[str, float]
    action_bias: Dict[str, float]


class ReflectionLoop:
    """Evaluates previous actions and adjusts future policy."""

    def __init__(self) -> None:
        self.bias: Dict[str, float] = {}

    def review(self, response: str, user_message: str, action: str) -> ReflectionResult:
        adjustments: Dict[str, float] = {}
        action_bias: Dict[str, float] = {}
        feedback_parts: List[str] = []
        if action == "ask_question" and "help" in user_message.lower():
            feedback_parts.append("Prioritize offering support when help is requested.")
            action_bias["offer_support"] = self.bias.get("offer_support", 0.0) + 0.2
        if action == "ask_question" and "thanks" in user_message.lower():
            feedback_parts.append("Acknowledge gratitude explicitly.")
            action_bias["offer_appreciation"] = self.bias.get("offer_appreciation", 0.0) + 0.1
        if not feedback_parts:
            feedback_parts.append("Response aligned with expectations.")
        self._apply_biases(action_bias)
        emit_state("reflection", response=response, feedback=feedback_parts, action_bias=self.bias)
        return ReflectionResult(feedback=" ".join(feedback_parts), adjustments=adjustments, action_bias=action_bias)

    def _apply_biases(self, action_bias: Dict[str, float]) -> None:
        for action, value in action_bias.items():
            self.bias[action] = value

    def get_bias(self, action: str) -> float:
        return self.bias.get(action, 0.0)


__all__ = ["ReflectionLoop", "ReflectionResult"]
