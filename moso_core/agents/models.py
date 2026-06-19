from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class GoalStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Goal:
    description: str
    status: GoalStatus = GoalStatus.PENDING
    created_at: str = ""
    owner_id: str = "default"
    goal_id: int | None = None
    completed_at: str | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Task:
    goal_id: int
    title: str
    description: str
    tool_name: str
    parameters: dict
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str | None = None
    task_id: int | None = None
    order: int = 0
    verification_method: str | None = None
    verification_target: str | None = None
    max_retries: int = 1
    retry_count: int = 0
    depends_on: list[int] | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["parameters"] = dict(self.parameters)
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class Plan:
    goal: Goal
    tasks: list[Task]
    estimated_steps: int
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "goal": self.goal.to_dict(),
            "tasks": [t.to_dict() for t in self.tasks],
            "estimated_steps": self.estimated_steps,
            "created_at": self.created_at,
        }

    def dry_run_summary(self) -> str:
        lines = [f"Goal: {self.goal.description}", "Plan:"]
        for i, task in enumerate(self.tasks, 1):
            action = task.parameters.get("action", "execute")
            target = task.parameters.get("path") or task.parameters.get("app_name") or task.parameters.get("command") or task.parameters.get("query") or task.parameters.get("url") or ""
            lines.append(f"")
            lines.append(f"  {i}. {task.title}")
            lines.append(f"     Tool: {task.tool_name}_tool")
            lines.append(f"     Action: {action}{' -> ' + target if target else ''}")
            if task.depends_on:
                lines.append(f"     Depends on: task(s) {[d + 1 for d in task.depends_on]}")
        lines.append("")
        lines.append("No actions executed.")
        lines.append("Proceed?")
        return "\n".join(lines)


@dataclass
class ExecutionSummary:
    goal: Goal
    task_results: list[dict]
    overall_status: GoalStatus
    started_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if self.overall_status in (GoalStatus.COMPLETED, GoalStatus.FAILED) and not self.completed_at:
            self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "goal": self.goal.to_dict(),
            "task_results": self.task_results,
            "overall_status": self.overall_status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
