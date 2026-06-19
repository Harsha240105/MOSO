from __future__ import annotations

import logging
import time
from typing import Optional

from moso_core.computer_use.models import ComputerUseResult

logger = logging.getLogger(__name__)


class KeyboardController:
    def __init__(self):
        self._pyautogui = None
        self._available = False
        self._import_pyautogui()

    def _import_pyautogui(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.05
            self._pyautogui = pyautogui
            self._available = True
        except ImportError:
            self._available = False
            logger.warning("pyautogui not available, keyboard controller disabled")

    @property
    def available(self) -> bool:
        return self._available

    def type_text(self, text: str, interval: float = 0.0) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.typewrite(text, interval=interval)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "type_text", {"length": len(text)}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "type_text", error=str(e), execution_time=elapsed)

    def press(self, key: str) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.press(key)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "press", {"key": key}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "press", error=str(e), execution_time=elapsed)

    def hotkey(self, *keys: str) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.hotkey(*keys)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "hotkey", {"keys": list(keys)}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "hotkey", error=str(e), execution_time=elapsed)

    def write(self, text: str) -> ComputerUseResult:
        return self.type_text(text)

    def ctrl_c(self) -> ComputerUseResult:
        return self.hotkey("ctrl", "c")

    def ctrl_v(self) -> ComputerUseResult:
        return self.hotkey("ctrl", "v")

    def alt_tab(self) -> ComputerUseResult:
        return self.hotkey("alt", "tab")

    def win_r(self) -> ComputerUseResult:
        return self.hotkey("win", "r")

    def enter(self) -> ComputerUseResult:
        return self.press("enter")

    def escape(self) -> ComputerUseResult:
        return self.press("escape")
