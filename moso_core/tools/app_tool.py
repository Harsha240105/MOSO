from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Optional

import psutil

from moso_core.tools.base import Tool
from moso_core.tools.models import ToolResult

logger = logging.getLogger(__name__)


class AppTool(Tool):
    name = "app_tool"
    description = "Launch, close, and list running applications"
    category = "app"
    permission_level = "guest"
    requires_confirmation = False

    _permission_map = {
        "launch_application": "trusted",
        "list_running_applications": "guest",
        "close_application": "owner",
    }

    def get_permission_level(self, action: str) -> str:
        return self._permission_map.get(action, "guest")

    def validate(self, **kwargs) -> tuple[bool, str]:
        return True, ""

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "list_running_applications")
        method = getattr(self, action, None)
        if method is None:
            return ToolResult(False, self.name, action, error=f"Unknown app action: {action}")
        return method(**{k: v for k, v in kwargs.items() if k != "action"})

    def launch_application(self, app_name: str, args: Optional[list[str]] = None) -> ToolResult:
        try:
            cmd: list[str] = []
            if os.name == "nt":
                cmd = ["cmd", "/c", "start", "", app_name]
            elif sys.platform == "darwin":
                cmd = ["open", "-a", app_name]
            else:
                binary = self._find_binary(app_name)
                if binary:
                    cmd = [binary]
                else:
                    cmd = ["xdg-open", app_name]

            if args:
                if os.name == "nt":
                    cmd.extend(args)
                else:
                    cmd.extend(args)

            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=os.name == "nt",
            )
            return ToolResult(True, self.name, "launch_application", result=f"Launched {app_name}")
        except Exception as e:
            return ToolResult(False, self.name, "launch_application", error=str(e))

    def close_application(self, app_name: str) -> ToolResult:
        try:
            closed = []
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info["name"] and app_name.lower() in proc.info["name"].lower():
                        proc.terminate()
                        closed.append(proc.info["name"])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if closed:
                return ToolResult(True, self.name, "close_application",
                                  result=f"Closed: {', '.join(set(closed))}")
            return ToolResult(False, self.name, "close_application",
                              error=f"No running process found matching '{app_name}'")
        except Exception as e:
            return ToolResult(False, self.name, "close_application", error=str(e))

    def list_running_applications(self) -> ToolResult:
        try:
            apps = []
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info["name"]:
                        apps.append({"pid": proc.info["pid"], "name": proc.info["name"]})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            apps.sort(key=lambda x: x["name"].lower())
            return ToolResult(True, self.name, "list_running_applications", result=apps[:200])
        except Exception as e:
            return ToolResult(False, self.name, "list_running_applications", error=str(e))

    def _find_binary(self, name: str) -> Optional[str]:
        import shutil
        return shutil.which(name)
