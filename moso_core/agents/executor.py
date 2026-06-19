from __future__ import annotations

import logging
import time

from moso_core.agents.models import ExecutionSummary, Goal, GoalStatus, Plan, Task, TaskStatus
from moso_core.agents.verifier import Verifier
from moso_core.tools.models import ToolRequest

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, tool_registry=None, identity=None, memory=None, resources=None):
        self._tool_registry = tool_registry
        self._identity = identity
        self._memory = memory
        self._resources = resources
        self._verifier = Verifier()

    @property
    def verifier(self) -> Verifier:
        return self._verifier

    def execute(self, plan: Plan, requester: str = "owner") -> ExecutionSummary:
        goal = plan.goal
        goal.status = GoalStatus.RUNNING
        task_results = []
        all_succeeded = True

        for task in plan.tasks:
            task.status = TaskStatus.RUNNING
            result = self._execute_task(task, requester)
            if result is None:
                task.status = TaskStatus.SKIPPED
                task_results.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "tool_name": task.tool_name,
                    "status": TaskStatus.SKIPPED.value,
                    "result": None,
                    "error": "No tool_registry available",
                })
                continue
            task.result = str(result.result) if result.success else None
            task.error = result.error
            if result.success and task.verification_method:
                verification = self._verifier.verify(task, result)
                if verification.success:
                    task.status = TaskStatus.COMPLETED
                    task_results.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "tool_name": task.tool_name,
                        "status": TaskStatus.COMPLETED.value,
                        "result": str(result.result) if result.result else None,
                        "error": None,
                        "verification": str(verification),
                    })
                else:
                    task.status = TaskStatus.FAILED
                    task.error = f"Verification failed: {verification}"
                    all_succeeded = False
                    task_results.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "tool_name": task.tool_name,
                        "status": TaskStatus.FAILED.value,
                        "result": str(result.result) if result.result else None,
                        "error": task.error,
                        "verification": str(verification),
                    })
            elif result.success:
                task.status = TaskStatus.COMPLETED
                task_results.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "tool_name": task.tool_name,
                    "status": TaskStatus.COMPLETED.value,
                    "result": str(result.result) if result.result else None,
                    "error": None,
                })
            else:
                task.status = TaskStatus.FAILED
                all_succeeded = False
                task_results.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "tool_name": task.tool_name,
                    "status": TaskStatus.FAILED.value,
                    "result": None,
                    "error": task.error,
                })
            if not result.success and task.status == TaskStatus.FAILED:
                logger.warning("Task '%s' failed: %s", task.title, task.error)

        goal.status = GoalStatus.COMPLETED if all_succeeded else GoalStatus.FAILED
        goal.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        return ExecutionSummary(
            goal=goal,
            task_results=task_results,
            overall_status=goal.status,
            completed_at=goal.completed_at or "",
        )

    def _execute_task(self, task: Task, requester: str):
        if self._tool_registry is None:
            logger.error("Cannot execute task: no tool_registry available")
            return None
        request = ToolRequest(
            tool_name=task.tool_name,
            parameters=task.parameters,
            requester=requester,
        )
        return self._tool_registry.execute_tool(
            request=request,
            identity=self._identity,
            memory=self._memory,
            resources=self._resources,
        )
