from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from moso_core.agents.executor import Executor
from moso_core.agents.history import PlanHistory
from moso_core.agents.manager import AgentManager
from moso_core.agents.models import Goal, GoalStatus, Plan, Task, TaskStatus
from moso_core.agents.planner import (
    CreateFileTemplate,
    CreateFolderTemplate,
    DesktopAutomationTemplate,
    OpenAppTemplate,
    Planner,
    PythonProjectTemplate,
    ReadFileTemplate,
    SearchWebTemplate,
)
from moso_core.computer_use.models import ComputerUseResult
from moso_core.tools.models import ToolRequest, ToolResult


class TestTaskRetry:
    def test_retry_default_max_retries(self):
        task = Task(goal_id=1, title="test", description="", tool_name="file", parameters={})
        assert task.max_retries == 1
        assert task.retry_count == 0

    def test_retry_custom_max_retries(self):
        task = Task(goal_id=1, title="test", description="", tool_name="file", parameters={}, max_retries=3)
        assert task.max_retries == 3

    def test_retry_increments_on_failure(self):
        mock_registry = MagicMock()
        mock_registry.execute_tool.return_value = ToolResult(
            success=False, tool_name="file", action="create_folder", error="fail"
        )
        executor = Executor(tool_registry=mock_registry)
        task = Task(
            goal_id=1, title="test", description="", tool_name="file",
            parameters={"action": "create_folder", "path": "/tmp/x"},
            max_retries=2, order=0,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert task.retry_count == 1
        assert task.status == TaskStatus.FAILED
        assert summary.overall_status == GoalStatus.FAILED

    def test_retry_succeeds_on_second_attempt(self):
        mock_registry = MagicMock()
        call_count = [0]

        def side_effect(request, identity=None, memory=None, resources=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return ToolResult(success=False, tool_name="file", action="create_folder", error="fail")
            return ToolResult(success=True, tool_name="file", action="create_folder", result="done")

        mock_registry.execute_tool.side_effect = side_effect
        executor = Executor(tool_registry=mock_registry)
        task = Task(
            goal_id=1, title="test", description="", tool_name="file",
            parameters={"action": "create_folder", "path": "/tmp/x"},
            max_retries=2, order=0,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert call_count[0] == 2
        assert task.status == TaskStatus.COMPLETED
        assert summary.overall_status == GoalStatus.COMPLETED

    def test_no_tool_registry_returns_skipped(self):
        executor = Executor(tool_registry=None)
        task = Task(goal_id=1, title="test", description="", tool_name="file", parameters={}, order=0)
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert task.status == TaskStatus.SKIPPED
        assert summary.overall_status == GoalStatus.FAILED


class TestTaskDependencies:
    def test_dependency_not_completed_skips_task(self):
        mock_registry = MagicMock()
        mock_registry.execute_tool.return_value = ToolResult(
            success=True, tool_name="file", action="create_folder", result="ok"
        )
        executor = Executor(tool_registry=mock_registry)
        task_a = Task(
            goal_id=1, title="task_a", description="", tool_name="file",
            parameters={"action": "create_folder", "path": "/tmp/a"},
            order=0,
        )
        task_b = Task(
            goal_id=1, title="task_b", description="", tool_name="file",
            parameters={"action": "create_file", "path": "/tmp/b"},
            order=1, depends_on=[5],
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task_a, task_b], estimated_steps=2)
        summary = executor.execute(plan)
        assert task_a.status == TaskStatus.COMPLETED
        assert task_b.status == TaskStatus.SKIPPED
        assert "not completed" in (task_b.error or "")

    def test_dependency_failed_skips_task(self):
        mock_registry = MagicMock()
        call_count = [0]

        def side_effect(request, identity=None, memory=None, resources=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return ToolResult(success=False, tool_name="file", action="create_folder", error="fail")
            return ToolResult(success=True, tool_name="file", action="create_file", result="ok")

        mock_registry.execute_tool.side_effect = side_effect
        executor = Executor(tool_registry=mock_registry)
        task_a = Task(
            goal_id=1, title="task_a", description="", tool_name="file",
            parameters={"action": "create_folder", "path": "/tmp/a"},
            max_retries=1, order=0,
        )
        task_b = Task(
            goal_id=1, title="task_b", description="", tool_name="file",
            parameters={"action": "create_file", "path": "/tmp/b"},
            order=1, depends_on=[0],
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task_a, task_b], estimated_steps=2)
        summary = executor.execute(plan)
        assert task_a.status == TaskStatus.FAILED
        assert task_b.status == TaskStatus.SKIPPED
        assert "failed" in (task_b.error or "").lower()

    def test_dependency_chain_succeeds(self):
        mock_registry = MagicMock()
        mock_registry.execute_tool.return_value = ToolResult(
            success=True, tool_name="file", action="create_folder", result="ok"
        )
        executor = Executor(tool_registry=mock_registry)
        task_a = Task(
            goal_id=1, title="task_a", description="", tool_name="file",
            parameters={"action": "create_folder", "path": "/tmp/a"},
            order=0,
        )
        task_b = Task(
            goal_id=1, title="task_b", description="", tool_name="file",
            parameters={"action": "create_file", "path": "/tmp/b"},
            order=1, depends_on=[0],
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task_a, task_b], estimated_steps=2)
        summary = executor.execute(plan)
        assert task_a.status == TaskStatus.COMPLETED
        assert task_b.status == TaskStatus.COMPLETED
        assert summary.overall_status == GoalStatus.COMPLETED


class TestDryRunSummary:
    def test_dry_run_summary_format(self):
        goal = Goal(description="create a python project named my_app")
        tasks = [
            Task(goal_id=0, title="Create project folder", description="", tool_name="file",
                 parameters={"action": "create_folder", "path": "my_app"}, order=0),
            Task(goal_id=0, title="Create __init__.py", description="", tool_name="file",
                 parameters={"action": "create_file", "path": "my_app/__init__.py"}, order=1,
                 depends_on=[0]),
        ]
        plan = Plan(goal=goal, tasks=tasks, estimated_steps=2)
        summary = plan.dry_run_summary()
        assert "Goal: create a python project named my_app" in summary
        assert "1. Create project folder" in summary
        assert "2. Create __init__.py" in summary
        assert "Tool: file_tool" in summary
        assert "Depends on: task(s) [1]" in summary
        assert "No actions executed." in summary
        assert "Proceed?" in summary

    def test_dry_run_summary_no_dependencies(self):
        goal = Goal(description="open notepad")
        tasks = [
            Task(goal_id=0, title="Launch application", description="", tool_name="app",
                 parameters={"action": "open", "app_name": "notepad"}, order=0),
        ]
        plan = Plan(goal=goal, tasks=tasks, estimated_steps=1)
        summary = plan.dry_run_summary()
        assert "Depends on" not in summary
        assert "Launch application" in summary


class TestPlanner:
    def test_python_project_template_scores_high(self):
        template = PythonProjectTemplate()
        score = template.score("create a python project named my_app")
        assert score >= 2

    def test_create_folder_template_scores_high(self):
        template = CreateFolderTemplate()
        score = template.score("create a folder named data")
        assert score >= 2

    def test_open_app_template_scores_high(self):
        template = OpenAppTemplate()
        score = template.score("open chrome browser")
        assert score >= 2

    def test_search_web_template_scores_high(self):
        template = SearchWebTemplate()
        score = template.score("search the web for python")
        assert score >= 2

    def test_read_file_template_scores_high(self):
        template = ReadFileTemplate()
        score = template.score("read the file README.md")
        assert score >= 2

    def test_create_file_template_scores_high(self):
        template = CreateFileTemplate()
        score = template.score("create a file named test.txt with content hello")
        assert score >= 2

    def test_planner_matches_python_project(self):
        planner = Planner()
        plan = planner.create_plan("create a python project named my_app")
        assert len(plan.tasks) == 3
        assert plan.tasks[0].tool_name == "file"
        assert plan.tasks[0].parameters["action"] == "create_folder"

    def test_planner_matches_open_app(self):
        planner = Planner()
        plan = planner.create_plan("open notepad")
        assert len(plan.tasks) == 1
        assert plan.tasks[0].tool_name == "app"
        assert plan.tasks[0].parameters["app_name"] == "notepad"

    def test_planner_falls_back_to_terminal(self):
        planner = Planner()
        plan = planner.create_plan("this is a completely unknown query that nothing matches")
        assert len(plan.tasks) == 1
        assert plan.tasks[0].tool_name == "terminal"

    def test_planner_sets_estimated_steps(self):
        planner = Planner()
        plan = planner.create_plan("create a python project named my_app")
        assert plan.estimated_steps == 3


class TestPlanHistory:
    def test_store_and_retrieve_goal(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        history = PlanHistory(db_path=db_path)
        try:
            goal = Goal(description="test goal")
            goal_id = history.store_goal(goal)
            assert goal_id > 0
            assert goal.goal_id == goal_id
            retrieved = history.get_goal(goal_id)
            assert retrieved is not None
            assert retrieved.description == "test goal"
            assert retrieved.status == GoalStatus.PENDING
        finally:
            history.close()
            os.unlink(db_path)

    def test_store_and_retrieve_task_with_new_columns(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        history = PlanHistory(db_path=db_path)
        try:
            goal = Goal(description="test")
            goal_id = history.store_goal(goal)
            task = Task(
                goal_id=goal_id, title="test task", description="desc",
                tool_name="file", parameters={"action": "create_folder"},
                order=0, max_retries=3, depends_on=[1, 2],
            )
            task_id = history.store_task(task)
            assert task_id > 0
            assert task.task_id == task_id
            tasks = history.get_tasks(goal_id)
            assert len(tasks) == 1
            assert tasks[0].max_retries == 3
            assert tasks[0].depends_on == [1, 2]
            assert tasks[0].retry_count == 0
        finally:
            history.close()
            os.unlink(db_path)

    def test_update_task_status(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        history = PlanHistory(db_path=db_path)
        try:
            goal = Goal(description="test")
            goal_id = history.store_goal(goal)
            task = Task(goal_id=goal_id, title="test", description="", tool_name="file",
                        parameters={}, order=0)
            history.store_task(task)
            task.status = TaskStatus.COMPLETED
            task.result = "success"
            history.update_task(task)
            tasks = history.get_tasks(goal_id)
            assert tasks[0].status == TaskStatus.COMPLETED
            assert tasks[0].result == "success"
        finally:
            history.close()
            os.unlink(db_path)

    def test_list_goals_ordered_by_recent(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        history = PlanHistory(db_path=db_path)
        try:
            g1 = history.store_goal(Goal(description="first"))
            g2 = history.store_goal(Goal(description="second"))
            goals = history.list_goals(limit=10)
            assert len(goals) >= 2
            assert goals[0].description == "second"
        finally:
            history.close()
            os.unlink(db_path)

    def test_get_recent_plans_includes_tasks(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        history = PlanHistory(db_path=db_path)
        try:
            goal = Goal(description="test")
            goal_id = history.store_goal(goal)
            task = Task(goal_id=goal_id, title="t1", description="", tool_name="file",
                        parameters={}, order=0)
            history.store_task(task)
            plans = history.get_recent_plans(limit=5)
            assert len(plans) >= 1
            assert len(plans[0].tasks) == 1
        finally:
            history.close()
            os.unlink(db_path)

    def test_cascade_delete(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        history = PlanHistory(db_path=db_path)
        try:
            goal = Goal(description="test")
            goal_id = history.store_goal(goal)
            history.store_task(Task(goal_id=goal_id, title="t1", description="",
                                    tool_name="file", parameters={}, order=0))
            history._conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
            history._conn.commit()
            tasks = history.get_tasks(goal_id)
            assert len(tasks) == 0
        finally:
            history.close()
            os.unlink(db_path)


class TestAgentManager:
    def test_plan_and_execute_creates_history(self):
        mock_registry = MagicMock()
        mock_registry.execute_tool.return_value = ToolResult(
            success=True, tool_name="file", action="create_folder", result="ok"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            manager = AgentManager(tool_registry=mock_registry, db_path=db_path)
            summary = manager.plan_and_execute("open notepad", requester="owner")
            assert summary.overall_status == GoalStatus.COMPLETED
            plans = manager.get_recent_plans(limit=5)
            assert len(plans) >= 1
            assert plans[0]["goal"]["description"] == "open notepad"
            manager._history.close()

    def test_preview_plan_returns_dry_run_summary(self):
        manager = AgentManager(tool_registry=None)
        preview = manager.preview_plan("open notepad")
        assert "Launch application" in preview
        assert "No actions executed." in preview
        assert "Proceed?" in preview

    def test_list_templates(self):
        manager = AgentManager(tool_registry=None)
        templates = manager.list_templates()
        assert len(templates) == 7
        names = [t["name"] for t in templates]
        assert "python_project" in names
        assert "open_app" in names
        assert "search_web" in names
        assert "desktop_automation" in names

    def test_create_plan_and_execute_no_registry_returns_failed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            manager = AgentManager(tool_registry=None, db_path=db_path)
            summary = manager.plan_and_execute("open notepad", requester="owner")
            assert summary.overall_status == GoalStatus.FAILED
            manager._history.close()


class TestVerifier:
    def test_verifier_file_exists(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"hello")
            path = f.name
        try:
            from moso_core.agents.verifier import Verifier
            verifier = Verifier()
            task = Task(goal_id=1, title="test", description="", tool_name="file",
                        parameters={}, verification_method="file_exists", verification_target=path)
            result = ToolResult(success=True, tool_name="file", action="create_file")
            vresult = verifier.verify(task, result)
            assert vresult.success is True
            assert "exists" in str(vresult)
        finally:
            os.unlink(path)

    def test_verifier_file_not_exists(self):
        from moso_core.agents.verifier import Verifier
        verifier = Verifier()
        task = Task(goal_id=1, title="test", description="", tool_name="file",
                    parameters={}, verification_method="file_exists",
                    verification_target="/nonexistent/path/xyz123")
        result = ToolResult(success=True, tool_name="file", action="create_file")
        vresult = verifier.verify(task, result)
        assert vresult.success is False


class TestDesktopAutomationTemplate:
    def test_screenshot_goal(self):
        template = DesktopAutomationTemplate()
        score = template.score("take a screenshot")
        assert score >= 2

    def test_type_goal(self):
        template = DesktopAutomationTemplate()
        score = template.score("type text on desktop")
        assert score >= 2

    def test_click_goal(self):
        template = DesktopAutomationTemplate()
        score = template.score("click mouse at 500 200")
        assert score >= 2

    def test_generates_screenshot_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="take a screenshot")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "capture_screen"

    def test_generates_type_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="type hello world")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "type_text"
        assert "hello" in tasks[0].parameters.get("text", "")

    def test_generates_click_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="click at 100 200")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "click"
        assert tasks[0].parameters["x"] == 100

    def test_generates_move_mouse_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="move mouse to 300 400")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "move_to"
        assert tasks[0].parameters["x"] == 300

    def test_generates_press_key_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="press enter")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "press"
        assert tasks[0].parameters["key"] == "enter"

    def test_generates_scroll_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="scroll down")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "scroll"
        assert tasks[0].parameters["amount"] > 0

    def test_generates_focus_window_task(self):
        template = DesktopAutomationTemplate()
        goal = Goal(description="focus chrome")
        tasks = template.generate(goal)
        assert len(tasks) == 1
        assert tasks[0].tool_name == "computer_use"
        assert tasks[0].parameters["action"] == "focus_window"
        assert "chrome" in tasks[0].parameters.get("window_title", "").lower()

    def test_planner_matches_desktop_automation(self):
        planner = Planner()
        plan = planner.create_plan("take a screenshot")
        assert plan.tasks[0].tool_name == "computer_use"


class TestExecutorComputerUseRouting:
    def test_computer_use_task_routed_to_automation(self):
        mock_automation = MagicMock()
        mock_automation.execute_action.return_value = ComputerUseResult(True, "click", result="ok")
        executor = Executor(automation_engine=mock_automation)
        task = Task(
            goal_id=1, title="test", description="", tool_name="computer_use",
            parameters={"action": "click", "x": 100, "y": 100},
            order=0,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert summary.overall_status == GoalStatus.COMPLETED
        mock_automation.execute_action.assert_called_once_with({"action": "click", "x": 100, "y": 100}, dry_run=False)

    def test_computer_use_task_no_engine_returns_skipped(self):
        executor = Executor(automation_engine=None)
        task = Task(
            goal_id=1, title="test", description="", tool_name="computer_use",
            parameters={"action": "click"},
            order=0,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert task.status == TaskStatus.SKIPPED

    def test_computer_use_sequence_routed(self):
        mock_automation = MagicMock()
        mock_automation.execute_sequence.return_value = [
            ComputerUseResult(True, "move_to", result="ok"),
            ComputerUseResult(True, "click", result="ok"),
        ]
        executor = Executor(automation_engine=mock_automation)
        task = Task(
            goal_id=1, title="test", description="", tool_name="computer_use",
            parameters={"action": "execute_sequence", "actions": [{"action": "move_to", "x": 100, "y": 100}, {"action": "click"}]},
            order=0,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert summary.overall_status == GoalStatus.COMPLETED
        mock_automation.execute_sequence.assert_called_once()

    def test_computer_use_dry_run_passthrough(self):
        mock_automation = MagicMock()
        mock_automation.execute_action.return_value = ComputerUseResult(True, "click", result="[DRY RUN] Would execute: click")
        executor = Executor(automation_engine=mock_automation)
        task = Task(
            goal_id=1, title="test", description="", tool_name="computer_use",
            parameters={"action": "click", "dry_run": True},
            order=0,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert summary.overall_status == GoalStatus.COMPLETED
        mock_automation.execute_action.assert_called_once_with({"action": "click", "dry_run": True}, dry_run=True)


class TestExecutorEdgeCases:
    def test_empty_task_list(self):
        executor = Executor(tool_registry=MagicMock())
        plan = Plan(goal=Goal(description="empty"), tasks=[], estimated_steps=0)
        summary = executor.execute(plan)
        assert summary.overall_status == GoalStatus.COMPLETED
        assert len(summary.task_results) == 0

    def test_executor_verification_passes(self):
        mock_registry = MagicMock()
        mock_registry.execute_tool.return_value = ToolResult(
            success=True, tool_name="file", action="create_file", result="ok"
        )
        executor = Executor(tool_registry=mock_registry)
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            path = f.name
        try:
            task = Task(
                goal_id=1, title="test", description="", tool_name="file",
                parameters={"action": "create_file", "path": path},
                order=0, verification_method="file_exists", verification_target=path,
            )
            plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
            summary = executor.execute(plan)
            assert task.status == TaskStatus.COMPLETED
        finally:
            os.unlink(path)

    def test_executor_verification_fails_with_retry(self):
        mock_registry = MagicMock()
        mock_registry.execute_tool.return_value = ToolResult(
            success=True, tool_name="file", action="create_file", result="ok"
        )
        executor = Executor(tool_registry=mock_registry)
        task = Task(
            goal_id=1, title="test", description="", tool_name="file",
            parameters={"action": "create_file", "path": "/nonexistent/test.py"},
            order=0, verification_method="file_exists", verification_target="/nonexistent/test.py",
            max_retries=2,
        )
        plan = Plan(goal=Goal(description="test"), tasks=[task], estimated_steps=1)
        summary = executor.execute(plan)
        assert task.status == TaskStatus.FAILED
        assert "Verification failed" in (task.error or "")
