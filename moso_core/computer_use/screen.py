from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Optional

from moso_core.computer_use.models import ComputerUseResult, ScreenCapture

logger = logging.getLogger(__name__)


class ScreenCapturer:
    def __init__(self, screenshot_dir: Optional[str] = None):
        self._mss = None
        self._pillow = None
        self._available = False
        self._screenshot_dir = screenshot_dir or os.path.join(os.path.expanduser("~"), ".moso", "screenshots")
        os.makedirs(self._screenshot_dir, exist_ok=True)
        self._import_libs()

    def _import_libs(self):
        try:
            import mss
            self._mss = mss
            from PIL import Image
            self._pillow = Image
            self._available = True
        except ImportError:
            self._available = False
            logger.warning("mss or Pillow not available, screen capturer disabled")

    @property
    def available(self) -> bool:
        return self._available

    def capture_screen(self) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            with self._mss.mss() as sct:
                monitor = sct.monitors[1]
                img = sct.grab(monitor)
                resolution = (img.width, img.height)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = os.path.join(self._screenshot_dir, f"screenshot_{timestamp}.png")
                self._pillow.frombytes("RGB", (img.width, img.height), img.rgb).save(path)
                elapsed = time.perf_counter() - start
                capture = ScreenCapture(
                    image_path=path,
                    resolution=resolution,
                )
                return ComputerUseResult(True, "capture_screen", capture.to_dict(), execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "capture_screen", error=str(e), execution_time=elapsed)

    def capture_region(self, left: int, top: int, width: int, height: int) -> ComputerUseResult:
        start = time.perf_counter()
        try:
            with self._mss.mss() as sct:
                monitor = {"left": left, "top": top, "width": width, "height": height}
                img = sct.grab(monitor)
                resolution = (img.width, img.height)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = os.path.join(self._screenshot_dir, f"region_{timestamp}.png")
                self._pillow.frombytes("RGB", (img.width, img.height), img.rgb).save(path)
                elapsed = time.perf_counter() - start
                capture = ScreenCapture(
                    image_path=path,
                    resolution=resolution,
                )
                return ComputerUseResult(True, "capture_region", capture.to_dict(), execution_time=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ComputerUseResult(False, "capture_region", error=str(e), execution_time=elapsed)

    def save_screenshot(self, path: str) -> ComputerUseResult:
        result = self.capture_screen()
        if result.success:
            import shutil
            try:
                shutil.move(result.result["image_path"], path)
                result.result["image_path"] = path
            except Exception as e:
                return ComputerUseResult(False, "save_screenshot", error=str(e))
        return result
