from __future__ import annotations

from enum import Enum


class OrbState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    EXECUTING = "executing"
    ERROR = "error"


class StatusColor(str, Enum):
    IDLE = "#6b7280"
    LISTENING = "#3b82f6"
    THINKING = "#22c55e"
    SPEAKING = "#a855f7"
    EXECUTING = "#eab308"
    ERROR = "#ef4444"
