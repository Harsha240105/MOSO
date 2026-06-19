from __future__ import annotations

import logging
from typing import Any, Optional

from moso_core.vision.context import build_context
from moso_core.vision.models import OCRResult, ScreenContext

logger = logging.getLogger(__name__)


class VisionManager:
    def __init__(self, identity=None, memory=None, resources=None, screen_capturer=None):
        self._identity = identity
        self._memory = memory
        self._resources = resources
        self._capturer = screen_capturer

    def _check_permission(self) -> tuple[bool, str]:
        if self._identity is None:
            return True, ""
        try:
            level = self._identity.get_identity_level()
            level_str = level.value.lower() if hasattr(level, "value") else str(level).lower()
            if level_str in ("owner", "trusted", "likely_owner"):
                return True, ""
            return False, f"Vision requires trusted or owner permission (current: {level_str})"
        except Exception as e:
            logger.warning("Identity check failed: %s", e)
            return False, f"Identity check failed: {e}"

    def _check_resources(self) -> bool:
        if self._resources is None:
            return True
        try:
            status = self._resources.get_system_status()
            cpu = getattr(status.cpu, "percent", 0) if status.cpu else 0
            ram = getattr(status.ram, "percent", 0) if status.ram else 0
            if cpu > 90 and ram > 90:
                logger.warning("Resources too low for OCR: CPU=%d%%, RAM=%d%%", cpu, ram)
                return False
            return True
        except Exception as e:
            logger.warning("Resource check failed: %s", e)
            return True

    def _store_memory_event(self, title: str, description: str, tags: list[str] | None = None):
        if self._memory is None:
            return
        try:
            self._memory.store_event(
                title=title,
                description=description[:500],
                tags=tags or ["vision"],
                owner_id="default",
            )
        except Exception as e:
            logger.warning("Failed to store vision memory event: %s", e)

    def capture_and_analyze(self) -> dict[str, Any]:
        allowed, reason = self._check_permission()
        if not allowed:
            return {"error": reason, "text": "", "regions": [], "windows": [], "active_window": "", "resolution": (0, 0)}
        do_ocr = self._check_resources()
        ctx = build_context(screen_capturer=self._capturer)
        result = ctx.to_dict()
        if not do_ocr:
            result["text"] = ""
            result["ocr_results"] = []
            result["ocr_skipped"] = "Resources too high"
        self._store_memory_event("Screen analyzed", ctx.summary(), ["vision", "screen-analysis"])
        return result

    def get_screen_text(self) -> str:
        allowed, reason = self._check_permission()
        if not allowed:
            return ""
        ctx = build_context(screen_capturer=self._capturer)
        self._store_memory_event("OCR performed", ctx.text_content[:200], ["vision", "ocr"])
        return ctx.text_content

    def get_active_window(self) -> str:
        allowed, reason = self._check_permission()
        if not allowed:
            return ""
        try:
            from moso_core.computer_use.windows import WindowManager
            wm = WindowManager()
            result = wm.get_active_window()
            if result.success and result.result:
                title = result.result.get("title", "")
                self._store_memory_event("Active window detected", title, ["vision", "window"])
                return title
        except Exception as e:
            logger.warning("Failed to get active window: %s", e)
        return ""

    def build_context(self) -> ScreenContext:
        allowed, reason = self._check_permission()
        if not allowed:
            return ScreenContext(text_content="", ocr_results=[], active_window="", windows=[])
        do_ocr = self._check_resources()
        ctx = build_context(screen_capturer=self._capturer)
        if not do_ocr:
            ctx.text_content = ""
            ctx.ocr_results = []
        return ctx
