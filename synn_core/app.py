"""Main application orchestrating the agent."""
from __future__ import annotations

import asyncio
import signal
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from .cognition import CognitionSubsystem
from .dialogue import DialogueManager
from .dreamer import Dreamer
from .emotions import HormoneSubsystem
from .interfaces import Event
from .logging_util import TRACE_BUFFER, RollingLog, cleanup_traces, setup_logging
from .memory import MemorySubsystem
from .needs import NeedsSubsystem
from .persona import PersonaSubsystem
from .reflection import ReflectionLoop
from .safety import EthicsEngine


@dataclass
class AgentConfig:
    trace_interval: float = 5.0
    dream_every: int = 5


class SynnCoreApp:
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self.config = config or AgentConfig()
        self.logger = setup_logging()
        self.memory = MemorySubsystem()
        self.hormones = HormoneSubsystem()
        self.needs = NeedsSubsystem()
        self.persona = PersonaSubsystem()
        self.cognition = CognitionSubsystem(self.memory, self.needs)
        self.reflection = ReflectionLoop()
        self.ethics = EthicsEngine()
        self.dialogue = DialogueManager(
            memory=self.memory,
            hormones=self.hormones,
            needs=self.needs,
            persona=self.persona,
            cognition=self.cognition,
            reflection=self.reflection,
            ethics=self.ethics,
        )
        self.dreamer = Dreamer(self.memory)
        self.rolling_log = RollingLog()
        self.turn_count = 0
        self._stop = False

    async def main_loop(self, events: AsyncIterator[Event]) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self.stop)
            except NotImplementedError:
                pass
        async for event in events:
            if self._stop:
                break
            turn = self.dialogue.process(event.payload)
            self.dialogue.reflect(turn)
            self.rolling_log.add(user=event.payload, agent=turn.agent_response)
            self.turn_count += 1
            if self.turn_count % self.config.dream_every == 0:
                self.dreamer.run()
            await asyncio.sleep(0.05)
        TRACE_BUFFER.flush()

    def stop(self) -> None:
        self._stop = True


async def _cli_runner(app: SynnCoreApp) -> None:
    async def generator() -> AsyncIterator[Event]:
        loop = asyncio.get_running_loop()
        prompt = "You: "
        while not app._stop:
            user_input = await loop.run_in_executor(None, input, prompt)
            yield Event(source="cli", payload=user_input)
            if user_input.strip().lower() in {"quit", "exit"}:
                app.stop()
                break

    await app.main_loop(generator())


def run_cli() -> None:
    cleanup_traces()
    app = SynnCoreApp()
    asyncio.run(_cli_runner(app))


__all__ = ["SynnCoreApp", "AgentConfig", "run_cli"]
