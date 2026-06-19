from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional


@dataclass
class ToolResult:
    success: bool
    tool_name: str
    action: str
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        if self.success:
            return f"[{self.tool_name}] {self.action}: {self.result}"
        return f"[{self.tool_name}] {self.action} FAILED: {self.error}"


@dataclass
class ToolRequest:
    tool_name: str
    parameters: dict = field(default_factory=dict)
    requester: str = "owner"
    timestamp: str = ""
    dry_run: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditEntry:
    timestamp: str
    tool: str
    action: str
    target: str
    result: str
    error: Optional[str] = None
    owner_id: str = "default"
    execution_time: float = 0.0
    trace_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
