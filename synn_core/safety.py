"""Safety and ethics module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .logging_util import emit_state


@dataclass
class EthicsDecision:
    action: str
    allowed: bool
    rationale: str
    mode: str  # "white_box" or "black_box"


class EthicsEngine:
    """Evaluates planned actions for alignment with safety principles."""

    def __init__(self) -> None:
        self.whitelist = {"offer_support", "share_learning", "ask_question", "address_curiosity", "address_social_connection", "address_competence", "address_safety", "offer_appreciation"}
        self.blacklist = {"share_sensitive_data"}

    def evaluate(self, action: str) -> EthicsDecision:
        if action in self.blacklist:
            decision = EthicsDecision(action=action, allowed=False, rationale="Action is explicitly disallowed", mode="white_box")
        elif action in self.whitelist:
            decision = EthicsDecision(action=action, allowed=True, rationale="Action within approved behaviors", mode="white_box")
        else:
            decision = EthicsDecision(action=action, allowed=True, rationale="No explicit rule; allowed with caution", mode="black_box")
        emit_state("ethics", action=action, allowed=decision.allowed, rationale=decision.rationale, mode=decision.mode)
        return decision


__all__ = ["EthicsEngine", "EthicsDecision"]
