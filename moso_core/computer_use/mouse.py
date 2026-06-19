from __future__ import annotations

import logging
import time

from moso_core.computer_use.models import ComputerUseResult

logger = logging.getLogger(__name__)


class MouseController:
    def __init__(self):
        self._pyautogui = None
        self._available = False
        self._import_pyautogui()

    def _import_pyautogui(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1
            self._pyautogui = pyautogui
            self._available = True
        except ImportError:
            self._available = False
            logger.warning("pyautogui not available, mouse controller disabled")

    @property
    def available(self) -> bool:
        return self._available

    def move_to(self, x: int, y: int, duration: float = 0.0) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.moveTo(x, y, duration=duration)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "move_to", {"x": x, "y": y}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "move_to", error=str(e), execution_time=elapsed)

    def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.click(x=x, y=y, button=button)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "click", {"x": x, "y": y, "button": button}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "click", error=str(e), execution_time=elapsed)

    def double_click(self, x: int | None = None, y: int | None = None) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.doubleClick(x=x, y=y)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "double_click", {"x": x, "y": y}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "double_click", error=str(e), execution_time=elapsed)

    def right_click(self, x: int | None = None, y: int | None = None) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.rightClick(x=x, y=y)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "right_click", {"x": x, "y": y}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "right_click", error=str(e), execution_time=elapsed)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.2) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.moveTo(start_x, start_y)
            self._pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "drag", {"from": {"x": start_x, "y": start_y}, "to": {"x": end_x, "y": end_y}}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "drag", error=str(e), execution_time=elapsed)

    def scroll(self, amount: int) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            self._pyautogui.scroll(amount)
            elapsed = time.perf_counter() - start
            return ComputerUseResult(True, "scroll", {"amount": amount}, execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "scroll", error=str(e), execution_time=elapsed)
