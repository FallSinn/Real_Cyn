"""Synn Core package providing the entry point for the agent system."""
from .app import run_cli, SynnCoreApp
from .scorecard import HumanityScorecard

__all__ = ["run_cli", "SynnCoreApp", "HumanityScorecard"]
