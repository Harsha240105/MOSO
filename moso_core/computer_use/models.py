from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional


@dataclass
class MouseAction:
    x: int
    y: int
    action_type: str = "click"
    button: str = "left"
    duration: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class KeyboardAction:
    action_type: str
    text: str = ""
    key: str = ""
    hotkey_combo: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v}


@dataclass
class ScreenCapture:
    image_path: str
    timestamp: str = ""
    resolution: tuple[int, int] = (0, 0)
    format: str = "png"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WindowAction:
    window_title: str
    action_type: str = "focus"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AutomationSequence:
    actions: list[dict] = field(default_factory=list)
    description: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComputerUseResult:
    success: bool
    action: str
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        if self.success:
            return f"[CU] {self.action}: {self.result}"
        return f"[CU] {self.action} FAILED: {self.error}"


@dataclass
class RecordedEvent:
    event_type: str
    data: dict
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)
