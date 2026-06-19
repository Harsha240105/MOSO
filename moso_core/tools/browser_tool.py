from __future__ import annotations

import logging
import urllib.parse
import webbrowser

from moso_core.tools.base import Tool
from moso_core.tools.models import ToolResult

logger = logging.getLogger(__name__)


class BrowserTool(Tool):
    name = "browser_tool"
    description = "Open URLs and search the web"
    category = "browser"
    permission_level = "guest"
    requires_confirmation = False

    def validate(self, **kwargs) -> tuple[bool, str]:
        return True, ""

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "open_url")
        method = getattr(self, action, None)
        if method is None:
            return ToolResult(False, self.name, action, error=f"Unknown browser action: {action}")
        return method(**{k: v for k, v in kwargs.items() if k != "action"})

    def open_url(self, url: str) -> ToolResult:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return ToolResult(True, self.name, "open_url", result=f"Opened {url}")
        except Exception as e:
            return ToolResult(False, self.name, "open_url", error=str(e))

    def search_web(self, query: str) -> ToolResult:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://duckduckgo.com/?q={encoded}"
            webbrowser.open(url)
            return ToolResult(True, self.name, "search_web", result=f"Searched: {query}")
        except Exception as e:
            return ToolResult(False, self.name, "search_web", error=str(e))
