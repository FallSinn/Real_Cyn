"""Interface stubs for external modalities."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Optional


class ASRInterface:
    """Mock automatic speech recognition interface."""

    async def transcribe(self) -> str:
        await asyncio.sleep(0.01)
        return "[ASR input unavailable in mock]"


class TTSInterface:
    """Mock text-to-speech interface."""

    async def speak(self, text: str) -> None:
        await asyncio.sleep(0.01)


class CVInterface:
    """Mock computer vision interface."""

    async def capture(self) -> str:
        await asyncio.sleep(0.01)
        return "[CV frame placeholder]"


@dataclass
class Event:
    """Representation of an event entering the agent system."""

    source: str
    payload: str


async def event_stream_cli(prompt: str) -> AsyncIterator[Event]:
    """CLI event stream generator."""

    while True:
        user_input = input(prompt)
        yield Event(source="cli", payload=user_input)


__all__ = ["ASRInterface", "TTSInterface", "CVInterface", "Event", "event_stream_cli"]
