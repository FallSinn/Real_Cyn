"""Self-test scenario demonstrating reflection adjustments."""
from __future__ import annotations

from synn_core.cognition import CognitionSubsystem
from synn_core.dialogue import DialogueManager
from synn_core.emotions import HormoneSubsystem
from synn_core.memory import MemorySubsystem
from synn_core.needs import NeedsSubsystem
from synn_core.persona import PersonaSubsystem
from synn_core.reflection import ReflectionLoop
from synn_core.safety import EthicsEngine
from synn_core.scorecard import HumanityScorecard


def run_scenario() -> None:
    memory = MemorySubsystem()
    memory.store.wipe()
    hormones = HormoneSubsystem()
    needs = NeedsSubsystem()
    persona = PersonaSubsystem()
    reflection = ReflectionLoop()
    reflection.bias["ask_question"] = 0.4
    cognition = CognitionSubsystem(memory, needs)
    ethics = EthicsEngine()
    scorecard = HumanityScorecard()
    manager = DialogueManager(memory, hormones, needs, persona, cognition, reflection, ethics, scorecard)

    dialogues = []
    for i in range(3):
        turn = manager.process("I need help figuring this out")
        dialogues.append(turn)
        manager.reflect(turn)

    first_action = dialogues[0].action
    second_action = dialogues[1].action
    third_action = dialogues[2].action

    assert first_action == "ask_question", f"Expected ask_question first, got {first_action}"
    assert second_action == "offer_support", f"Expected offer_support second, got {second_action}"
    assert third_action == "offer_support", f"Expected offer_support third, got {third_action}"

    print("Self-test complete")
    for turn in dialogues:
        print(f"User: {turn.user_message} -> Action: {turn.action}")


if __name__ == "__main__":
    run_scenario()
