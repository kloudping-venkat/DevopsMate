"""
DevopsMate Agent - 4-Mode Operating System

Modes:
- ASK: Read-only intelligence & answers (Safe)
- PLAN: Change simulation & recommendations (Medium)
- DEBUG: Deep inspection & diagnostics (Elevated)
- EXECUTE: Makes real changes (High)
"""

from .base import AgentMode, ModeCapability, ModeResult, AgentContext
from .ask import AskMode
from .plan import PlanMode
from .debug import DebugMode
from .execute import ExecuteMode

__all__ = [
    "AgentMode",
    "ModeCapability",
    "ModeResult",
    "AgentContext",
    "AskMode",
    "PlanMode",
    "DebugMode",
    "ExecuteMode",
]
