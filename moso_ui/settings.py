from __future__ import annotations

import json
import os
from typing import Optional

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".moso", "aura_settings.json")


class AuraSettings:
    def __init__(self):
        self.orb_x: int = -1
        self.orb_y: int = -1
        self.model_path: str = ""
        self.server_port: int = 8081
        self.auto_start_server: bool = False
        self.n_ctx: int = 2048
        self.max_tokens: int = 512
        self.temperature: float = 0.7
        self.bubble_auto_hide: int = 0
        self.always_on_top: bool = True
        self.load()

    def load(self):
        try:
            if os.path.isfile(SETTINGS_PATH):
                with open(SETTINGS_PATH) as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(self, k):
                        setattr(self, k, v)
        except Exception:
            pass

    def save(self):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump(self.__dict__, f, indent=2)
