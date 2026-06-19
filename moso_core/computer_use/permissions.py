from __future__ import annotations

from typing import Any, Optional

PERMISSION_LEVELS: dict[str, list[str]] = {
    "guest": ["screenshot", "list_windows"],
    "trusted": ["screenshot", "list_windows", "focus_window", "get_active_window"],
    "owner": [
        "screenshot", "list_windows", "focus_window", "get_active_window", "close_window",
        "move_mouse", "click", "double_click", "right_click", "drag", "scroll",
        "type_text", "press_key", "hotkey",
        "record_mouse", "record_keyboard", "execute_sequence",
    ],
}


class ComputerUsePermissions:
    def __init__(self, identity: Any = None):
        self._identity = identity

    def check(self, action: str, identity: Any = None) -> tuple[bool, str]:
        ident = identity or self._identity
        for level, actions in PERMISSION_LEVELS.items():
            if action in actions:
                if level == "guest":
                    return True, ""
                if level == "trusted":
                    if ident is None:
                        return False, "Trusted-level permission requires identity engine"
                    level_str = self._get_identity_level(ident)
                    if level_str in ("owner", "likely_owner"):
                        return True, ""
                    return False, f"Trusted-level '{action}' requires likely_owner or owner identity"
                if level == "owner":
                    if ident is None:
                        return False, "Owner-level permission requires identity engine"
                    if self._is_owner(ident):
                        return True, ""
                    return False, f"Owner-level '{action}' requires full owner verification"
        return False, f"Unknown action: {action}"

    def get_allowed_actions(self, identity: Any = None) -> list[str]:
        ident = identity or self._identity
        if ident is None:
            return list(PERMISSION_LEVELS["guest"])
        level_str = self._get_identity_level(ident)
        if self._is_owner(ident):
            return list(PERMISSION_LEVELS["owner"])
        if level_str in ("owner", "likely_owner"):
            return list(PERMISSION_LEVELS["trusted"])
        return list(PERMISSION_LEVELS["guest"])

    def _get_identity_level(self, identity) -> str:
        try:
            level = identity.get_identity_level()
            if hasattr(level, "value"):
                return level.value.lower()
            return str(level).lower()
        except Exception:
            return "unknown"

    def _is_owner(self, identity) -> bool:
        try:
            return bool(identity.is_owner())
        except Exception:
            return False
