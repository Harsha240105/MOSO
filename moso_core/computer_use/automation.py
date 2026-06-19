from __future__ import annotations

import logging
import time
from typing import Any, Optional

from moso_core.computer_use.keyboard import KeyboardController
from moso_core.computer_use.models import ComputerUseResult
from moso_core.computer_use.mouse import MouseController
from moso_core.computer_use.permissions import ComputerUsePermissions
from moso_core.computer_use.screen import ScreenCapturer
from moso_core.computer_use.windows import WindowManager

logger = logging.getLogger(__name__)

ACTION_MAP: dict[str, str] = {
    "move_to": "move_mouse",
    "click": "click",
    "double_click": "double_click",
    "right_click": "right_click",
    "drag": "drag",
    "scroll": "scroll",
    "type_text": "type_text",
    "press": "press_key",
    "hotkey": "hotkey",
    "capture_screen": "screenshot",
    "capture_region": "screenshot",
    "list_windows": "list_windows",
    "get_active_window": "list_windows",
    "focus_window": "focus_window",
    "close_window": "close_window",
}


class AutomationEngine:
    def __init__(
        self,
        identity: Any = None,
        memory: Any = None,
        resources: Any = None,
    ):
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._screen = ScreenCapturer()
        self._windows = WindowManager()
        self._permissions = ComputerUsePermissions()
        self._identity = identity
        self._memory = memory
        self._resources = resources

    @property
    def mouse(self) -> MouseController:
        return self._mouse

    @property
    def keyboard(self) -> KeyboardController:
        return self._keyboard

    @property
    def screen(self) -> ScreenCapturer:
        return self._screen

    @property
    def windows(self) -> WindowManager:
        return self._windows

    def execute_action(self, action: dict, dry_run: bool = False) -> ComputerUseResult:
        action_type = action.get("action", "")
        perm_name = ACTION_MAP.get(action_type, action_type)
        allowed, reason = self._permissions.check(perm_name, self._identity)
        if not allowed:
            return ComputerUseResult(False, action_type, error=f"Permission denied: {reason}")

        if dry_run:
            target = action.get("target") or action.get("text") or action.get("key") or action.get("window_title") or ""
            return ComputerUseResult(True, action_type, result=f"[DRY RUN] Would execute: {action_type}{' -> ' + str(target) if target else ''}")

        if self._resources and action_type in ("type_text", "hotkey", "drag", "execute_sequence"):
            try:
                status = self._resources.get_system_status()
                cpu = getattr(status.cpu, "percent", 0) if status.cpu else 0
                ram = getattr(status.ram, "percent", 0) if status.ram else 0
                battery = getattr(getattr(status, "battery", None), "percent", 100) if hasattr(status, "battery") else 100
                if cpu > 90 and ram > 90:
                    logger.warning("System resources low: CPU=%d%%, RAM=%d%%", cpu, ram)
            except Exception as e:
                logger.warning("Resource check failed: %s", e)

        router = {
            "move_to": lambda: self._mouse.move_to(action.get("x", 0), action.get("y", 0), action.get("duration", 0.0)),
            "click": lambda: self._mouse.click(action.get("x"), action.get("y"), action.get("button", "left")),
            "double_click": lambda: self._mouse.double_click(action.get("x"), action.get("y")),
            "right_click": lambda: self._mouse.right_click(action.get("x"), action.get("y")),
            "drag": lambda: self._mouse.drag(action.get("start_x", 0), action.get("start_y", 0), action.get("end_x", 0), action.get("end_y", 0), action.get("duration", 0.2)),
            "scroll": lambda: self._mouse.scroll(action.get("amount", 0)),
            "type_text": lambda: self._keyboard.type_text(action.get("text", ""), action.get("interval", 0.0)),
            "press": lambda: self._keyboard.press(action.get("key", "")),
            "hotkey": lambda: self._keyboard.hotkey(*action.get("keys", [])),
            "capture_screen": lambda: self._screen.capture_screen(),
            "capture_region": lambda: self._screen.capture_region(action.get("left", 0), action.get("top", 0), action.get("width", 100), action.get("height", 100)),
            "list_windows": lambda: self._windows.list_windows(),
            "get_active_window": lambda: self._windows.get_active_window(),
            "focus_window": lambda: self._windows.focus_window(action.get("window_title", "")),
            "close_window": lambda: self._windows.close_window(action.get("window_title", "")),
        }
        handler = router.get(action_type)
        if handler is None:
            return ComputerUseResult(False, action_type, error=f"Unknown action: {action_type}")

        result = handler()

        if result.success and self._memory and hasattr(self._memory, "store_event"):
            try:
                target_desc = action.get("text") or action.get("key") or action.get("window_title") or action.get("x", "")
                tags = ["computer-use", action_type]
                if target_desc:
                    tags.append(str(target_desc).lower()[:30])
                self._memory.store_event(
                    title=f"Computer Use: {action_type}",
                    description=str(result.result)[:500] if result.result else action_type,
                    tags=tags,
                    owner_id="default",
                )
            except Exception as e:
                logger.warning("Failed to log computer use event to memory: %s", e)

        return result

    def execute_sequence(self, sequence: list[dict], dry_run: bool = False) -> list[ComputerUseResult]:
        if dry_run:
            results = []
            for i, action in enumerate(sequence, 1):
                action_type = action.get("action", "?")
                target = action.get("target") or action.get("text") or action.get("key") or action.get("window_title") or action.get("app_name") or ""
                results.append(ComputerUseResult(True, action_type, result=f"[{i}] {action_type}{' -> ' + str(target) if target else ''}"))
            return results

        results = []
        for action in sequence:
            result = self.execute_action(action, dry_run=False)
            results.append(result)
            if not result.success:
                logger.warning("Sequence halted at action '%s': %s", action.get("action"), result.error)
                break
        return results

    def dry_run_sequence(self, sequence: list[dict]) -> str:
        lines = ["Computer Use Plan:"]
        for i, action in enumerate(sequence, 1):
            action_type = action.get("action", "?")
            target = action.get("text") or action.get("key") or action.get("window_title") or action.get("app_name") or ""
            param_str = f" -> {target}" if target else ""
            lines.append(f"  {i}. {action_type}{param_str}")
        lines.append("")
        lines.append("No actions executed.")
        lines.append("Proceed?")
        return "\n".join(lines)
