from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from typing import Optional

from moso_core.agents.models import Goal, GoalStatus, Plan, Task, TaskStatus

logger = logging.getLogger(__name__)


class PlanHistory:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, ".moso")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "plans.db")
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self):
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_tables()

    def _init_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                owner_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tool_name TEXT NOT NULL,
                parameters TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                error TEXT,
                task_order INTEGER NOT NULL DEFAULT 0,
                verification_method TEXT,
                verification_target TEXT,
                max_retries INTEGER NOT NULL DEFAULT 1,
                retry_count INTEGER NOT NULL DEFAULT 0,
                depends_on TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            );
        """)
        self._conn.commit()

    def store_goal(self, goal: Goal) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO goals (description, status, owner_id, created_at, completed_at) VALUES (?, ?, ?, ?, ?)",
                (goal.description, goal.status.value, goal.owner_id, goal.created_at, goal.completed_at),
            )
            self._conn.commit()
            goal_id = cur.lastrowid
            goal.goal_id = goal_id
            logger.info("Stored goal %d: %s", goal_id, goal.description[:60])
            return goal_id

    def update_goal(self, goal: Goal) -> None:
        if goal.goal_id is None:
            return
        with self._lock:
            self._conn.execute(
                "UPDATE goals SET status=?, completed_at=? WHERE id=?",
                (goal.status.value, goal.completed_at, goal.goal_id),
            )
            self._conn.commit()

    def store_task(self, task: Task) -> int:
        params_json = json.dumps(task.parameters) if isinstance(task.parameters, dict) else task.parameters
        depends_on_json = json.dumps(task.depends_on) if task.depends_on is not None else None
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO tasks (goal_id, title, description, tool_name, parameters, status, result, error, task_order, verification_method, verification_target, max_retries, retry_count, depends_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (task.goal_id, task.title, task.description, task.tool_name, params_json, task.status.value, task.result, task.error, task.order, task.verification_method, task.verification_target, task.max_retries, task.retry_count, depends_on_json),
            )
            self._conn.commit()
            task.task_id = cur.lastrowid
            return task.task_id

    def update_task(self, task: Task) -> None:
        if task.task_id is None:
            return
        with self._lock:
            self._conn.execute(
                "UPDATE tasks SET status=?, result=?, error=? WHERE id=?",
                (task.status.value, task.result, task.error, task.task_id),
            )
            self._conn.commit()

    def get_goal(self, goal_id: int) -> Optional[Goal]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
            if row is None:
                return None
            return Goal(
                goal_id=row["id"],
                description=row["description"],
                status=GoalStatus(row["status"]),
                owner_id=row["owner_id"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )

    def get_tasks(self, goal_id: int) -> list[Task]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM tasks WHERE goal_id=? ORDER BY task_order", (goal_id,)).fetchall()
            return [self._row_to_task(r) for r in rows]

    def list_goals(self, limit: int = 20) -> list[Goal]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM goals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [
                Goal(
                    goal_id=r["id"],
                    description=r["description"],
                    status=GoalStatus(r["status"]),
                    owner_id=r["owner_id"],
                    created_at=r["created_at"],
                    completed_at=r["completed_at"],
                )
                for r in rows
            ]

    def get_recent_plans(self, limit: int = 5) -> list[Plan]:
        goals = self.list_goals(limit=limit)
        plans = []
        for goal in goals:
            if goal.goal_id is None:
                continue
            tasks = self.get_tasks(goal.goal_id)
            plans.append(Plan(goal=goal, tasks=tasks, estimated_steps=len(tasks)))
        return plans

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        params = row["parameters"]
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                params = {}
        depends_on_raw = row["depends_on"]
        depends_on = None
        if depends_on_raw:
            try:
                depends_on = json.loads(depends_on_raw)
            except (json.JSONDecodeError, TypeError):
                depends_on = None
        return Task(
            task_id=row["id"],
            goal_id=row["goal_id"],
            title=row["title"],
            description=row["description"] or "",
            tool_name=row["tool_name"],
            parameters=params,
            status=TaskStatus(row["status"]),
            result=row["result"],
            error=row["error"],
            order=row["task_order"],
            verification_method=row["verification_method"],
            verification_target=row["verification_target"],
            max_retries=row["max_retries"],
            retry_count=row["retry_count"],
            depends_on=depends_on,
        )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("PlanHistory closed")
