from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

from moso_core.tools.models import AuditEntry, ToolResult

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, ".moso")
            os.makedirs(data_dir, exist_ok=True)
            log_path = os.path.join(data_dir, "tools-audit.log")
        self._log_path = log_path

    def log(self, entry: AuditEntry) -> None:
        try:
            line = entry.to_json()
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError as e:
            logger.warning("Audit log write failed: %s", e)

    def log_tool_result(self, result: ToolResult, tool_name: str, action: str,
                        target: str = "", owner_id: str = "default") -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            tool=tool_name,
            action=action,
            target=target,
            result="success" if result.success else "error",
            error=result.error,
            owner_id=owner_id,
            execution_time=result.execution_time,
        )
        self.log(entry)
        return entry

    def recent(self, count: int = 20) -> list[AuditEntry]:
        entries: list[AuditEntry] = []
        try:
            if not os.path.exists(self._log_path):
                return entries
            with open(self._log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            entries.append(AuditEntry(**data))
                        except (json.JSONDecodeError, TypeError):
                            continue
        except OSError as e:
            logger.warning("Audit log read failed: %s", e)
        return entries[-count:]

    def clear(self) -> None:
        try:
            if os.path.exists(self._log_path):
                os.remove(self._log_path)
                logger.info("Audit log cleared: %s", self._log_path)
        except OSError as e:
            logger.warning("Audit log clear failed: %s", e)

    @property
    def log_path(self) -> str:
        return self._log_path
