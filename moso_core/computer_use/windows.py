from __future__ import annotations

import logging
from typing import Optional

from moso_core.computer_use.models import ComputerUseResult

logger = logging.getLogger(__name__)


class WindowManager:
    def __init__(self):
        self._pygetwindow = None
        self._available = False
        self._import_pygetwindow()

    def _import_pygetwindow(self):
        try:
            import pygetwindow
            self._pygetwindow = pygetwindow
            self._available = True
        except ImportError:
            self._available = False
            logger.warning("pygetwindow not available, window manager disabled")

    @property
    def available(self) -> bool:
        return self._available

    def list_windows(self) -> ComputerUseResult:
        try:
            titles = self._pygetwindow.getAllTitles()
            titles = [t for t in titles if t.strip()]
            return ComputerUseResult(True, "list_windows", {"windows": titles})
        except Exception as e:
            return ComputerUseResult(False, "list_windows", error=str(e))

    def get_active_window(self) -> ComputerUseResult:
        try:
            win = self._pygetwindow.getActiveWindow()
            if win is None:
                return ComputerUseResult(False, "get_active_window", error="No active window found")
            return ComputerUseResult(True, "get_active_window", {"title": win.title, "size": (win.width, win.height)})
        except Exception as e:
            return ComputerUseResult(False, "get_active_window", error=str(e))

    def focus_window(self, title: str) -> ComputerUseResult:
        try:
            wins = self._pygetwindow.getWindowsWithTitle(title)
            if not wins:
                return ComputerUseResult(False, "focus_window", error=f"No window found matching '{title}'")
            wins[0].activate()
            return ComputerUseResult(True, "focus_window", {"title": title})
        except Exception as e:
            return ComputerUseResult(False, "focus_window", error=str(e))

    def close_window(self, title: str) -> ComputerUseResult:
        try:
            wins = self._pygetwindow.getWindowsWithTitle(title)
            if not wins:
                return ComputerUseResult(False, "close_window", error=f"No window found matching '{title}'")
            wins[0].close()
            return ComputerUseResult(True, "close_window", {"title": title})
        except Exception as e:
            return ComputerUseResult(False, "close_window", error=str(e))
