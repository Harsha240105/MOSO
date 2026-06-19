from __future__ import annotations

import logging
from typing import Any, Optional

from moso_core.agents.executor import ExecutionSummary, Executor
from moso_core.agents.history import PlanHistory
from moso_core.agents.models import GoalStatus, Plan
from moso_core.agents.planner import Planner

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(
        self,
        tool_registry=None,
        identity=None,
        memory=None,
        resources=None,
        db_path: Optional[str] = None,
    ):
        self._planner = Planner()
        self._executor = Executor(
            tool_registry=tool_registry,
            identity=identity,
            memory=memory,
            resources=resources,
        )
        self._history = PlanHistory(db_path=db_path)

    @property
    def planner(self) -> Planner:
        return self._planner

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def history(self) -> PlanHistory:
        return self._history

    def create_plan(self, description: str, owner_id: str = "default") -> Plan:
        return self._planner.create_plan(description, owner_id=owner_id)

    def execute_plan(self, plan: Plan, requester: str = "owner") -> ExecutionSummary:
        goal_id = self._history.store_goal(plan.goal)
        for task in plan.tasks:
            task.goal_id = goal_id
            self._history.store_task(task)
        summary = self._executor.execute(plan, requester=requester)
        self._history.update_goal(summary.goal)
        for task in plan.tasks:
            self._history.update_task(task)
        logger.info(
            "Plan execution completed: %s (%s)",
            summary.goal.description[:60],
            summary.overall_status.value,
        )
        return summary

    def plan_and_execute(self, description: str, requester: str = "owner") -> ExecutionSummary:
        plan = self.create_plan(description, owner_id=requester)
        return self.execute_plan(plan, requester=requester)

    def get_recent_plans(self, limit: int = 5) -> list[dict]:
        plans = self._history.get_recent_plans(limit=limit)
        return [p.to_dict() for p in plans]

    def list_templates(self) -> list[dict]:
        return [
            {"name": "python_project", "description": "Create a Python project structure with __init__.py and main.py"},
            {"name": "create_folder", "description": "Create a folder or directory"},
            {"name": "open_app", "description": "Open or launch an application"},
            {"name": "search_web", "description": "Search the web or browse a URL"},
            {"name": "read_file", "description": "Read a file"},
            {"name": "create_file", "description": "Create a file with optional content"},
        ]
