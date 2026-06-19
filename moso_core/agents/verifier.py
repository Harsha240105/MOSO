from __future__ import annotations

import logging
import os

from moso_core.agents.models import Task, TaskStatus
from moso_core.tools.models import ToolResult

logger = logging.getLogger(__name__)


class VerificationResult:
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

    def __bool__(self) -> bool:
        return self.success

    def __str__(self) -> str:
        return self.message


class Verifier:
    def verify(self, task: Task, tool_result: ToolResult) -> VerificationResult:
        if not tool_result.success:
            return VerificationResult(False, f"Tool execution failed: {tool_result.error}")

        method = task.verification_method
        target = task.verification_target

        if method == "file_exists":
            return self._verify_file_exists(target)
        if method == "folder_exists":
            return self._verify_folder_exists(target)
        if method == "exit_code_zero":
            return self._verify_exit_code(tool_result)
        if method == "process_running":
            return self._verify_process_running(target)
        if method == "content_not_empty":
            return self._verify_content_not_empty(tool_result)

        return VerificationResult(True, "No verification required")

    def _verify_file_exists(self, path: str | None) -> VerificationResult:
        if not path:
            return VerificationResult(False, "No path specified for file existence check")
        exists = os.path.exists(path)
        return VerificationResult(exists, f"File {path} {'exists' if exists else 'does not exist'}")

    def _verify_folder_exists(self, path: str | None) -> VerificationResult:
        if not path:
            return VerificationResult(False, "No path specified for folder existence check")
        is_dir = os.path.isdir(path)
        return VerificationResult(is_dir, f"Folder {path} {'exists' if is_dir else 'does not exist'}")

    def _verify_exit_code(self, tool_result: ToolResult) -> VerificationResult:
        if not tool_result.result or not isinstance(tool_result.result, dict):
            return VerificationResult(False, "No result data to check exit code")
        exit_code = tool_result.result.get("exit_code", -1)
        return VerificationResult(exit_code == 0, f"Exit code: {exit_code}")

    def _verify_process_running(self, name: str | None) -> VerificationResult:
        if not name:
            return VerificationResult(False, "No process name specified")
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                try:
                    if proc.info["name"] and name.lower() in proc.info["name"].lower():
                        return VerificationResult(True, f"Process '{name}' is running")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return VerificationResult(False, f"No running process found matching '{name}'")
        except Exception as e:
            return VerificationResult(False, f"Process check failed: {e}")

    def _verify_content_not_empty(self, tool_result: ToolResult) -> VerificationResult:
        if tool_result.result and len(str(tool_result.result)) > 0:
            return VerificationResult(True, "Content is not empty")
        return VerificationResult(False, "Content is empty")
