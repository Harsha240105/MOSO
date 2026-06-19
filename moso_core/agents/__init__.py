from moso_core.agents.base import Agent, AgentResult, SimpleAgent, ToolSpec

try:
    from moso_core.agents.manager import AgentManager
    from moso_core.agents.models import ExecutionSummary, Goal, GoalStatus, Plan, Task, TaskStatus
    from moso_core.agents.planner import Planner
    from moso_core.agents.executor import Executor
    from moso_core.agents.verifier import Verifier
    from moso_core.agents.history import PlanHistory

    AGENTS_AVAILABLE = True
except ImportError:
    AgentManager = None  # noqa: F811
    Planner = None  # noqa: F811
    Executor = None  # noqa: F811
    Verifier = None  # noqa: F811
    PlanHistory = None  # noqa: F811
    AGENTS_AVAILABLE = False

__all__ = [
    "Agent",
    "AgentResult",
    "SimpleAgent",
    "ToolSpec",
    "AgentManager",
    "Planner",
    "Executor",
    "Verifier",
    "PlanHistory",
    "ExecutionSummary",
    "Goal",
    "GoalStatus",
    "Plan",
    "Task",
    "TaskStatus",
    "AGENTS_AVAILABLE",
]
