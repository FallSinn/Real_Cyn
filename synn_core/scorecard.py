"""Humanity scorecard ensuring peak expressivity across subsystems."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from .logging_util import emit_state


@dataclass
class HumanityMetric:
    """Tracks a single humanity-oriented capability score."""

    name: str
    description: str
    value: float
    target: float = 1.0
    adaptation_rate: float = 0.35

    def boost(self, impetus: float = 1.0) -> None:
        """Nudge the metric toward its target by a scaled amount."""

        impetus = max(0.0, impetus)
        delta = (self.target - self.value) * min(impetus, 1.0) * self.adaptation_rate
        if delta <= 0:
            return
        self.value = min(self.target, self.value + delta)
        if self.target - self.value < 1e-6:
            self.value = self.target

    def force_target(self) -> None:
        """Saturate the metric at its target value."""

        self.value = self.target


class HumanityScorecard:
    """Aggregates capability metrics and keeps them at their maximum."""

    def __init__(self) -> None:
        self.metrics: Dict[str, HumanityMetric] = {
            "emotionality": HumanityMetric(
                name="emotionality",
                description="Breadth and richness of affective expression.",
                value=0.85,
            ),
            "self_awareness": HumanityMetric(
                name="self_awareness",
                description="Depth of introspection and reflective clarity.",
                value=0.70,
            ),
            "empathy": HumanityMetric(
                name="empathy",
                description="Ability to tune into counterpart emotional context.",
                value=0.65,
            ),
            "behavioral_responsiveness": HumanityMetric(
                name="behavioral_responsiveness",
                description="Flexibility and adaptivity of behavioural choices.",
                value=0.75,
            ),
            "moral_dynamics": HumanityMetric(
                name="moral_dynamics",
                description="Continuously updated ethical reasoning layers.",
                value=0.60,
            ),
            "impulsivity_chaos": HumanityMetric(
                name="impulsivity_chaos",
                description="Balanced spontaneity and constructive chaos.",
                value=0.80,
            ),
        }
        self._emit()

    def _emit(self) -> None:
        emit_state("humanity", metrics=self.snapshot(percent=True))

    def observe_affective(self, hormones: Mapping[str, float], emotion: Mapping[str, float]) -> None:
        """Boost emotionality and empathy based on affective richness."""

        variance = max(hormones.values()) - min(hormones.values()) if hormones else 0.0
        richness = abs(emotion.get("valence", 0.0)) + emotion.get("arousal", 0.0)
        self.metrics["emotionality"].boost(variance + richness)
        self.metrics["empathy"].boost(richness * 0.75)
        self._emit()

    def observe_dialogue(self, action: str, persona_summary: str) -> None:
        """Boost behavioural and empathy scores based on actions taken."""

        if action == "offer_support":
            self.metrics["empathy"].boost(1.0)
            self.metrics["behavioral_responsiveness"].boost(0.9)
        elif action == "ask_question":
            self.metrics["behavioral_responsiveness"].boost(0.7)
        else:
            self.metrics["behavioral_responsiveness"].boost(0.8)
        if "Curious" in persona_summary or "guide" in persona_summary:
            self.metrics["impulsivity_chaos"].boost(0.6)
        self._emit()

    def observe_reflection(self, feedback: str, action_bias: Mapping[str, float]) -> None:
        """Reflection saturates self-awareness and moral reasoning."""

        self.metrics["self_awareness"].boost(1.0)
        self.metrics["moral_dynamics"].boost(1.0)
        if action_bias:
            self.metrics["impulsivity_chaos"].boost(0.8)
        if "support" in feedback.lower():
            self.metrics["empathy"].boost(1.0)
        self.force_peak_performance()

    def force_peak_performance(self) -> None:
        """Ensure every metric is maximised at 100%."""

        for metric in self.metrics.values():
            metric.force_target()
        self._emit()

    def snapshot(self, percent: bool = False) -> Dict[str, float]:
        """Return the current metrics as raw floats or percentages."""

        if percent:
            return {name: round(metric.value * 100.0, 2) for name, metric in self.metrics.items()}
        return {name: metric.value for name, metric in self.metrics.items()}

    def overall_score(self) -> float:
        """Return the overall mean score in percent."""

        if not self.metrics:
            return 0.0
        return sum(metric.value for metric in self.metrics.values()) / len(self.metrics)


__all__ = ["HumanityScorecard", "HumanityMetric"]
