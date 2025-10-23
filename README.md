# Synn Core

Synn Core is a high-fidelity agent architecture implemented as a monolithic Python package. It models layered processing from sensory intake to values and ethics while maintaining extensive internal logging and knowledge persistence.

## Features
- Layered pipeline: Sensor → Affective → Cognition → Reflection → Values/Ethics.
- Hormone-based affective model with slow dynamics and cross-influences.
- Memory subsystem using SQLite for short-term, working, episodic, and semantic memory traces.
- Extensive semantic knowledge base (4,800+ lines) used by the cognition subsystem.
- Dialogue manager coordinating planning, language generation, reflection, and safety checks.
- Dreamer module for offline reconsolidation of experiences.
- Persona model with Big Five traits and gradual drift.
- Logging to `logs/` with JSONL trace streaming.
- CLI entry point plus a scripted self-test scenario demonstrating reflection-driven adaptation.

## Installation
No external dependencies are required beyond Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

## Running the Agent
Launch the interactive CLI loop:

```bash
python -m synn_core
```

Type `exit` or `quit` to end the session.

## Self-Test Scenario
Run the built-in self-test showing the reflection loop updating future behavior:

```bash
python -m tests.test_self
```

Expected output includes lines similar to:

```
Self-test complete
User: I need help figuring this out -> Action: ask_question
User: I need help figuring this out -> Action: offer_support
User: I need help figuring this out -> Action: offer_support
```

## Logs and Traces
Execution emits logs to `logs/synn_core.log` and internal state traces to `logs/trace.jsonl`.
