from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from moso_core.tools.models import ToolResult


class Tool(ABC):
    name: str = ""
    description: str = ""
    category: str = "general"
    permission_level: str = "guest"
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        ...

    @abstractmethod
    def validate(self, **kwargs) -> tuple[bool, str]:
        ...

    def get_permission_level(self, action: str) -> str:
        return self.permission_level

    def describe_action(self, **kwargs) -> str:
        target = ""
        for key in ("path", "app_name", "url", "command", "query", "name", "source", "pattern"):
            if key in kwargs and kwargs[key]:
                target = str(kwargs[key])
                break
        name = kwargs.get("_action_name", kwargs.get("action", "execute"))
        if target:
            return f"{self.name}: {name} -> {target}"
        return f"{self.name}: {name}"
