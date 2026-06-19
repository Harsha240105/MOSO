from __future__ import annotations

import logging
from typing import Any, Optional

from moso_core.vision.models import OCRResult, WindowInfo
from moso_core.vision.ocr import extract_text, extract_text_regions

logger = logging.getLogger(__name__)


def analyze_screenshot(screen_capturer=None) -> dict[str, Any]:
    capturer = screen_capturer
    if capturer is None:
        try:
            from moso_core.computer_use.screen import ScreenCapturer
            capturer = ScreenCapturer()
        except Exception:
            logger.warning("No screen capturer available")
            return {
                "text": "",
                "regions": [],
                "windows": [],
                "active_window": "",
                "resolution": (0, 0),
                "error": "No screen capturer available",
            }

    capture_result = capturer.capture_screen()
    if not capture_result.success:
        logger.warning("Screenshot capture failed: %s", capture_result.error)
        return {
            "text": "",
            "regions": [],
            "windows": [],
            "active_window": "",
            "resolution": (0, 0),
            "error": capture_result.error,
        }

    image_path = None
    resolution = (0, 0)
    if capture_result.result:
        image_path = capture_result.result.get("image_path")
        res_tuple = capture_result.result.get("resolution")
        if res_tuple and len(res_tuple) == 2:
            resolution = (int(res_tuple[0]), int(res_tuple[1]))

    text = ""
    regions: list[OCRResult] = []
    if image_path:
        try:
            from PIL import Image
            image = Image.open(image_path)
            text = extract_text(image)
            regions = extract_text_regions(image)
            image.close()
        except Exception as e:
            logger.warning("OCR analysis failed: %s", e)

    windows_info = []
    active_window_title = ""
    try:
        from moso_core.computer_use.windows import WindowManager
        wm = WindowManager()
        list_result = wm.list_windows()
        if list_result.success and list_result.result:
            w = list_result.result.get("windows", [])
            windows_info = w
        active_result = wm.get_active_window()
        if active_result.success and active_result.result:
            active_window_title = active_result.result.get("title", "")
    except Exception as e:
        logger.warning("Window detection failed: %s", e)

    return {
        "text": text,
        "regions": [r.to_dict() for r in regions],
        "windows": windows_info,
        "active_window": active_window_title,
        "resolution": resolution,
    }
